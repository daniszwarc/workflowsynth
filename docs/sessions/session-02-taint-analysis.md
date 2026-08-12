# WorkflowSynth — Session 02: Taint Analysis Engine

**Date:** August 6, 2026
**DSR Phase:** Build (Week 28)
**Component:** Verification Module — Stage 1 (Taint Analysis)
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Implement the taint analysis engine: the second half of Stage 1 verification.
After this session, the DSL Layer is fully complete and every workflow candidate
produced by the LLM is verified for both type safety (Session 01) and data flow
security (Session 02) before it proceeds to test execution.

By the end of this session we have:

- `src/verification/__init__.py` — public interface of the Verification module
- `src/verification/taint.py` — taint analysis engine
- `tests/unit/test_taint.py` — taint analysis unit tests

---

## What Taint Analysis Does (and Why It Exists)

The type checker (Session 01) answers: "are the types compatible?"
The taint analyser answers: "can we trust where this data came from?"

These are orthogonal questions. A workflow can be perfectly type-safe and still
be insecure -- for example, fetching data from an external API and writing it
directly to a database without validating it first. The types match, but the
data is untrusted.

Taint analysis tracks data provenance through the workflow. Every piece of data
that enters from an external source is marked as "tainted" -- untrusted. For
tainted data to reach a critical sink (a write or external call), it must first
pass through a sanitiser that validates or transforms it. If it reaches a sink
without being sanitised, the taint analyser rejects the workflow and returns an
error for the LLM repair prompt.

This is what the system catches:

```
fetch_api    →  🔴 tainted (external source)
write_database  ←  REJECTED (tainted data reached a sink without sanitising)
```

This is what it allows:

```
fetch_api       →  🔴 tainted
validate_schema →  ✅ sanitised (taint removed)
write_database  →  ✅ allowed  (clean data)
```

The dissertation justification is Tihanyi et al. (2025) FormAI-v2: 62% of
LLM-generated programs contain formally verified vulnerabilities. Taint analysis
is the mechanism that catches this class of vulnerability at the DSL level,
before the workflow is ever translated to n8n or LangChain.

---

## Taint Analysis Definitions

### Sources -- ops that introduce tainted (untrusted) data

Any step using these operators produces tainted output, regardless of context:

```python
TAINT_SOURCES = {
    "fetch_api",       # external API -- response is untrusted
    "read_database",   # DB record -- may contain user-supplied data
    "call_webhook",    # external webhook response -- untrusted
    "call_subworkflow" # subworkflow output -- provenance unknown
}
```

### Sinks -- ops where tainted data must NEVER arrive

If a tainted variable reaches one of these ops as input, the workflow is rejected:

```python
TAINT_SINKS = {
    "write_database",  # writing untrusted data to DB = injection risk
    "call_webhook",    # sending untrusted data externally = data leakage
    "send_to_queue",   # publishing untrusted data = injection into queue
    "notify_user",     # sending untrusted data to user = content injection
    "log_audit",       # logging untrusted data = log injection
}
```

Note: `call_webhook` appears in both sets. When used as a source, its output
variable is tainted. When used as a sink, its input must be clean.

### Sanitisers -- ops that remove taint

After passing through one of these ops, the output variable is no longer tainted:

```python
TAINT_SANITISERS = {
    "validate_schema",  # validates structure and types -- removes taint
    "encrypt_field",    # encrypts sensitive data -- removes taint
    "transform_json",   # reshapes data -- removes taint (with caveat, see below)
    "filter_records",   # filters records by condition -- removes taint
    "extract_field",    # extracts a specific field -- removes taint
}
```

**Important caveat on `transform_json` and `filter_records`:** In a production
system, transforming or filtering data does not automatically make it safe --
the transformation itself could be vulnerable. For WorkflowSynth v1, we treat
these as sanitisers because the DSL constrains what transformations are possible.
This is a known limitation, logged in the Implementation Journal.

---

## Algorithm

The taint analyser makes a single forward pass through the ordered steps of the
`WorkflowAST`. It maintains a set of "tainted variables" -- output variable names
whose data is untrusted. At each step:

1. If the step's op is a **source**: mark its output variable as tainted.
2. If the step's op is a **sink**: check if `params.input` is a tainted variable.
   If yes, record a violation.
3. If the step's op is a **sanitiser**: if `params.input` was tainted, the output
   variable is clean -- remove the taint.
4. Otherwise: if the step has an input and it was tainted, and the step has an
   output, propagate the taint to the output (taint flows through neutral ops).

This is a conservative approximation -- it may flag some safe workflows as
violations. That is the correct trade-off for a security-first system: false
positives are acceptable; false negatives (missing a real vulnerability) are not.

---

## File 1: `src/verification/__init__.py`

```python
# src/verification/__init__.py
# Public interface of the Verification Module.

from .taint import taint_analysis, TaintViolation

__all__ = [
    "taint_analysis",
    "TaintViolation",
]
```

---

## File 2: `src/verification/taint.py`

```python
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
            step_id=step.step_id if hasattr(step, 'step_id') else step.id,
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
```

---

## File 3: `tests/unit/test_taint.py`

```python
# tests/unit/test_taint.py
#
# Unit tests for the taint analysis engine.
# Each test covers a specific data flow scenario.

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.verification.taint import taint_analysis, TaintViolation


def _parse(yaml_string: str):
    """Helper: parses YAML and returns the AST. Asserts parsing succeeds."""
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed: {result.get('errors')}"
    return result["ast"]


# --- No violations (safe workflows) -----------------------------------------

def test_clean_workflow_no_sources():
    """A workflow with no sources has no tainted data -- no violations."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: authenticate_user
    params:
      role: admin
  - id: s2
    op: write_database
    params:
      table: logs
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_source_sanitised_before_sink():
    """fetch_api -> validate_schema -> write_database: taint removed. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/invoices"
    output: raw_data
  - id: s2
    op: validate_schema
    params:
      input: raw_data
      schema: invoice_schema
    output: clean_data
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: clean_data
      table: invoices
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_source_encrypted_before_sink():
    """fetch_api -> encrypt_field -> write_database: encrypted = sanitised. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: encrypt_field
    params:
      input: raw
    output: encrypted
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: encrypted
      table: secure_table
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_read_database_sanitised_before_webhook():
    """read_database -> transform_json -> call_webhook: taint removed. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: read_database
    params:
      table: orders
    output: raw_orders
  - id: s2
    op: transform_json
    params:
      input: raw_orders
    output: transformed
  - id: s3
    op: authenticate_user
    params:
      role: system
  - id: s4
    op: call_webhook
    params:
      input: transformed
      url: "https://partner.example.com/orders"
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_filter_records_as_sanitiser():
    """filter_records is a valid sanitiser -- removes taint."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: filter_records
    params:
      input: raw
    output: filtered
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: filtered
      table: t
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


# --- Violations (unsafe workflows) ------------------------------------------

def test_fetch_direct_to_write_database():
    """
    fetch_api -> write_database with no sanitiser.
    Classic taint violation: unsanitised external data written to DB.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/data"
    output: raw_data
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      input: raw_data
      table: my_table
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].step_id == "s3"
    assert violations[0].op == "write_database"
    assert violations[0].tainted_var == "raw_data"
    assert violations[0].taint_origin == "s1"


def test_read_database_direct_to_send_to_queue():
    """read_database -> send_to_queue with no sanitiser. Violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: read_database
    params:
      table: users
    output: user_data
  - id: s2
    op: send_to_queue
    params:
      input: user_data
      queue: outbound
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "user_data"


def test_taint_propagates_through_neutral_op():
    """
    fetch_api -> aggregate_data (neutral) -> write_database.
    Taint propagates through aggregate_data (not a sanitiser).
    Violation at write_database.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: aggregate_data
    params:
      input: raw
    output: aggregated
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: aggregated
      table: t
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "aggregated"
    # Taint origin is still s1 (where taint was introduced)
    assert violations[0].taint_origin == "s1"


def test_multiple_violations_in_one_workflow():
    """
    Two sinks receiving tainted data. Both violations reported in one pass.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: notify_user
    params:
      input: raw
  - id: s3
    op: send_to_queue
    params:
      input: raw
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 2
    ops = {v.op for v in violations}
    assert "notify_user" in ops
    assert "send_to_queue" in ops


def test_taint_stops_after_sanitiser():
    """
    fetch_api -> validate_schema -> aggregate_data -> write_database.
    validate_schema removes taint. aggregate_data operates on clean data.
    write_database receives clean data. No violation.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: validate_schema
    params:
      input: raw
      schema: s
    output: clean
  - id: s3
    op: aggregate_data
    params:
      input: clean
    output: summary
  - id: s4
    op: authenticate_user
    params:
      role: admin
  - id: s5
    op: write_database
    params:
      input: summary
      table: t
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_call_webhook_as_source_then_sink():
    """
    call_webhook output is tainted (it is a source).
    A second call_webhook receiving that tainted output is a violation.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: call_webhook
    params:
      url: "https://partner.example.com/data"
    output: partner_data
  - id: s2
    op: authenticate_user
    params:
      role: system
  - id: s3
    op: call_webhook
    params:
      input: partner_data
      url: "https://internal.example.com/ingest"
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "partner_data"


def test_no_taint_without_output():
    """
    A source step with no declared output produces no named tainted variable.
    No taint to propagate.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/ping"
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      table: logs
"""
    ast = _parse(yaml)
    # s1 has no output -- no tainted variable introduced
    # s3 has no input -- not checking any variable
    assert taint_analysis(ast) == []
```

---

## File structure to create in the repo

```
workflowsynth/
  src/
    verification/
      __init__.py
      taint.py
  tests/
    unit/
      test_taint.py
```

The `src/dsl/` files from Session 01 remain unchanged.

---

## Integration with Session 01

After Session 02, Stage 1 verification is complete. The two checkers are
independent and can be called together:

```python
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.dsl.type_checker import type_check
from workflowsynth.verification.taint import taint_analysis

def stage_1_verify(yaml_string: str) -> dict:
    """
    Full Stage 1 verification: parse + type check + taint analysis.
    Returns a dict with the combined results.
    """
    # Parse
    parse_result = parse_workflow(yaml_string)
    if not parse_result["ok"]:
        return {
            "passed": False,
            "parse_errors": parse_result["errors"],
            "type_errors": [],
            "taint_violations": [],
        }

    ast = parse_result["ast"]

    # Type check
    type_errors = type_check(ast)

    # Taint analysis
    taint_violations = taint_analysis(ast)

    return {
        "passed": not type_errors and not taint_violations,
        "parse_errors": [],
        "type_errors": type_errors,
        "taint_violations": [v.message for v in taint_violations],
    }
```

This `stage_1_verify()` function is what the LangGraph `verify_dsl` node will
call. Its output maps directly to the `WorkflowSynthState` fields:
`dsl_verification_passed`, `dsl_type_errors`, `dsl_taint_violations`.

---

## How to run the tests

```bash
# from the repo root
pytest tests/unit/ -v
```

All 20 tests from Session 01 plus the new taint tests should pass.

---

## Implementation Journal

```
Date: 2026-08-06
DSR Phase: Build
Component: Verification Module -- Taint Analysis
Type: Decision
Description: transform_json and filter_records included as sanitisers.
Justification: The DSL constrains what transformations are possible -- the
  25-primitive vocabulary does not permit arbitrary code injection through
  transform_json or filter_records. Treating them as sanitisers is safe
  within the constraints of WorkflowSynth v1.
Dissertation Impact: Known limitation -- Section 7 (Limitations). Note that
  in a general-purpose language, transformation alone does not sanitise.
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Verification Module -- Taint Analysis
Type: Decision
Description: Taint analysis reports ALL violations in a single forward pass,
  not stopping at the first one.
Justification: Reporting all violations in one pass gives the LLM repair
  prompt more information, improving the likelihood of a correct repair in
  the next attempt. This is consistent with how the type checker works.
Dissertation Impact: Repair loop efficiency -- Section 5 (Implementation).
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Verification Module -- Taint Analysis
Type: Decision
Description: call_webhook appears in both TAINT_SOURCES and TAINT_SINKS.
Justification: As a source, call_webhook returns external data of unknown
  provenance (tainted). As a sink, it sends data externally (risk of data
  leakage if tainted). Both roles are valid and non-contradictory.
Dissertation Impact: Security model -- Section 5 (Implementation).
```

---

## Next Session

Session 03 -- LangGraph Pipeline (`src/synthesis/state.py`,
`src/synthesis/nodes.py`, `src/synthesis/pipeline.py`).

Stage 1 verification is now complete. The next session wires the DSL Layer
and Verification Module into the LangGraph synthesis loop.
