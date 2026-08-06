# src/verification/taint.py
#
# Taint analysis engine for WorkflowSynth.
# Operates on WorkflowAST -- never on raw dicts.
#
# Tracks untrusted data (taint) from sources through the workflow.
# Rejects any workflow where tainted data reaches a critical sink
# without passing through a sanitiser.
#
# Usage:
#   from workflowsynth.verification.taint import taint_analysis
#   violations = taint_analysis(ast)
#   if violations:
#       # feed violations to repair prompt

from dataclasses import dataclass
from ..dsl.ast_nodes import WorkflowAST, WorkflowStep


# --- Vocabulary definitions --------------------------------------------------
#
# These sets define the security model.
# Any change here requires a journal entry and test suite update.

# Ops whose output is always untrusted (external or unknown provenance)
TAINT_SOURCES: set[str] = {
    "fetch_api",
    "read_database",
    "call_webhook",
    "call_subworkflow",
}

# Ops where tainted input is a security violation
TAINT_SINKS: set[str] = {
    "write_database",
    "call_webhook",
    "send_to_queue",
    "notify_user",
    "log_audit",
}

# Ops that remove taint from their output
# (input was tainted, output is clean after this op)
TAINT_SANITISERS: set[str] = {
    "validate_schema",
    "encrypt_field",
    "transform_json",
    "filter_records",
    "extract_field",
}


# --- TaintViolation dataclass ------------------------------------------------

@dataclass
class TaintViolation:
    """
    A taint violation: tainted data reached a critical sink.

    Fields:
        step_id:        ID of the sink step where the violation was detected.
        op:             The sink operator.
        tainted_var:    Name of the variable that carried the taint.
        taint_origin:   ID of the source step that introduced the taint.
        message:        Human-readable error for the LLM repair prompt.
    """
    step_id: str
    op: str
    tainted_var: str
    taint_origin: str
    message: str


# --- Main entry point --------------------------------------------------------

def taint_analysis(ast: WorkflowAST) -> list[TaintViolation]:
    """
    Runs taint analysis on a WorkflowAST.

    Returns a list of TaintViolation objects (empty = no violations = taint-safe).
    Each violation carries a message suitable for inclusion in a repair prompt.

    The analysis is a single forward pass through the ordered steps.
    Time complexity: O(n) where n is the number of steps.
    """
    violations: list[TaintViolation] = []

    # tainted_vars: maps variable_name -> step_id that introduced the taint
    # Using a dict (not a set) so we can report where the taint originated.
    tainted_vars: dict[str, str] = {}

    for step in ast.steps:
        _process_step(step, tainted_vars, violations)

    return violations


# --- Step processing ---------------------------------------------------------

def _process_step(
    step: WorkflowStep,
    tainted_vars: dict[str, str],
    violations: list[TaintViolation],
) -> None:
    """
    Processes a single step, updating tainted_vars and recording any violations.
    Mutates both tainted_vars and violations in place.
    """
    input_var = step.params.get("input")
    input_is_tainted = input_var is not None and input_var in tainted_vars

    # --- Sink check (highest priority -- check before anything else) ---------
    # If this op is a sink and receives tainted input, record a violation.
    if step.op in TAINT_SINKS and input_is_tainted:
        taint_origin = tainted_vars[input_var]
        violations.append(TaintViolation(
            step_id=step.id,
            op=step.op,
            tainted_var=input_var,
            taint_origin=taint_origin,
            message=(
                f"Step '{step.id}' (op: {step.op}): "
                f"tainted variable '{input_var}' reached a sink without sanitisation. "
                f"Taint introduced at step '{taint_origin}' via a source operation. "
                f"Add a sanitising step (validate_schema, encrypt_field, transform_json, "
                f"filter_records, or extract_field) between step '{taint_origin}' "
                f"and step '{step.id}'."
            )
        ))
        # Do not return -- continue processing so we catch all violations
        # in a single pass (better repair prompts).

    # --- Source: mark output as tainted --------------------------------------
    if step.op in TAINT_SOURCES and step.output is not None:
        tainted_vars[step.output] = step.id

    # --- Sanitiser: output is clean even if input was tainted ----------------
    elif step.op in TAINT_SANITISERS and step.output is not None:
        # Remove taint from the output variable (even if input was tainted)
        # The sanitiser breaks the taint chain.
        if step.output in tainted_vars:
            del tainted_vars[step.output]
        # Explicitly ensure this output is not in tainted_vars
        # (it should not be, but defensive programming)
        tainted_vars.pop(step.output, None)

    # --- Taint propagation: neutral ops pass taint through -------------------
    # If this op is neither a source, sanitiser, nor sink, and its input
    # was tainted, the taint propagates to its output.
    elif input_is_tainted and step.output is not None:
        tainted_vars[step.output] = tainted_vars[input_var]
