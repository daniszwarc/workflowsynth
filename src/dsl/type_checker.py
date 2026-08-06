# src/dsl/type_checker.py
#
# Type safety checker for WorkflowSynth.
# Operates on WorkflowAST -- never on raw dicts.
#
# Verifies:
#   1. Type flow between steps (output -> input compatibility)
#   2. Security rule: authenticate_user precedes write_database and call_webhook
#
# Returns a list of structured errors for the repair prompt.

from .ast_nodes import WorkflowAST, WorkflowStep
from .constants import OP_OUTPUT_TYPES, OPS_REQUIRING_INPUT, OPS_REQUIRING_AUTH


def type_check(ast: WorkflowAST) -> list[str]:
    """
    Runs the full type checker on a WorkflowAST.

    Returns a list of errors (empty = no errors = type-safe).
    Errors are written to be useful in a repair prompt.
    """
    errors = []
    errors.extend(_check_type_flow(ast))
    errors.extend(_check_auth_rule(ast))
    return errors


# --- Check 1: type flow ------------------------------------------------------

def _check_type_flow(ast: WorkflowAST) -> list[str]:
    """
    Verifies that every params.input reference points to an output declared
    by a previous step, and that the types are compatible.

    We build a map of output_var -> output_type as we advance through the steps.
    Each step that references an input checks against this map.
    A step can only reference outputs from steps that come before it.
    """
    errors = []
    available_outputs: dict[str, str] = {}  # var_name -> output_type

    for step in ast.steps:
        errors.extend(_check_step_input(step, available_outputs))

        # register this step's output for subsequent steps
        if step.output is not None:
            output_type = OP_OUTPUT_TYPES.get(step.op, "any")
            available_outputs[step.output] = output_type

    return errors


def _check_step_input(
    step: WorkflowStep,
    available_outputs: dict[str, str]
) -> list[str]:
    """Validates the input reference for a single step."""
    errors = []

    if step.op not in OPS_REQUIRING_INPUT:
        return errors  # this op does not require a declared input

    input_var = step.params.get("input")

    # op requires input but it is not declared
    if input_var is None:
        errors.append(
            f"Step '{step.id}' (op: {step.op}): "
            f"missing required param 'input'. "
            f"This op requires an input from a previous step's output."
        )
        return errors

    # referenced input does not exist in previous outputs
    if input_var not in available_outputs:
        errors.append(
            f"Step '{step.id}' (op: {step.op}): "
            f"input '{input_var}' is not defined. "
            f"Available outputs at this point: "
            f"{sorted(available_outputs.keys()) or 'none'}. "
            f"Make sure the step that produces '{input_var}' comes before "
            f"this step and declares 'output: {input_var}'."
        )
        return errors

    # check type compatibility
    input_type = available_outputs[input_var]
    type_error = _check_type_compatibility(step.op, input_type, input_var)
    if type_error:
        errors.append(f"Step '{step.id}': {type_error}")

    return errors


def _check_type_compatibility(op: str, input_type: str, input_var: str) -> str | None:
    """
    Verifies that the input type is compatible with what the op expects.
    Returns an error message if incompatible, None if compatible.
    """
    # Operators that require a list of records as input
    REQUIRE_RECORDS = {
        "filter_records", "transform_json", "validate_schema",
        "aggregate_data", "format_output",
    }
    # Operators that require a string as input
    REQUIRE_STRING = {
        "encrypt_field",
    }

    if op in REQUIRE_RECORDS and input_type not in ("records", "any"):
        return (
            f"op '{op}' requires input of type 'records' "
            f"but '{input_var}' has type '{input_type}'. "
            f"Make sure the step producing '{input_var}' uses an op "
            f"that outputs a list of records (e.g. fetch_api, filter_records, "
            f"validate_schema, read_database)."
        )

    if op in REQUIRE_STRING and input_type not in ("string", "any"):
        return (
            f"op '{op}' requires input of type 'string' "
            f"but '{input_var}' has type '{input_type}'."
        )

    return None


# --- Check 2: authentication rule --------------------------------------------

def _check_auth_rule(ast: WorkflowAST) -> list[str]:
    """
    Verifies that any write_database or call_webhook has a preceding
    authenticate_user step in the workflow.

    CONSTRAINT (Architectural Decision 3):
    authenticate_user must precede any write or webhook operation.
    This rule prevents unauthenticated data from reaching critical sinks.

    We verify that at least one authenticate_user step exists somewhere
    BEFORE the problematic step. We do not require the auth output to be
    the direct input of the write step -- that would be too restrictive
    for complex workflows with multiple branches.
    """
    errors = []
    auth_seen = False

    for step in ast.steps:
        if step.op == "authenticate_user":
            auth_seen = True
            continue

        if step.op in OPS_REQUIRING_AUTH and not auth_seen:
            errors.append(
                f"Step '{step.id}' (op: {step.op}): "
                f"no 'authenticate_user' step found before this operation. "
                f"Security rule: authenticate_user must precede "
                f"write_database and call_webhook. "
                f"Add an authenticate_user step before step '{step.id}'."
            )

    return errors
