# WorkflowSynth — Session 01: DSL Layer

**Date:** August 6, 2026
**DSR Phase:** Build (Week 28)
**Component:** DSL Layer
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Implement the complete DSL Layer: the parser that converts LLM-generated YAML into a typed internal AST, and the type checker that validates the type flow across the 25 primitives.

By the end of this session we have:

- `src/dsl/constants.py` — the 25-operator vocabulary with type signatures
- `src/dsl/ast_nodes.py` — internal workflow representation (dataclasses)
- `src/dsl/parser.py` — parses LLM YAML output into a `WorkflowAST`
- `src/dsl/type_checker.py` — validates types and security rules on the AST
- `tests/unit/test_parser.py` — parser unit tests
- `tests/unit/test_type_checker.py` — type checker unit tests

---

## Why the DSL Layer Exists

The LLM produces text. Free-form, unpredictable text that can invent operations that don't exist, chain steps in incompatible ways, or produce insecure data flows. The DSL Layer is the first line of defence: it converts that text into a structured, verifiable representation, or fails explicitly with errors that the synthesis engine can feed back to the LLM as a repair prompt.

Without the DSL Layer, the system has nothing to reason about formally.

---

## Architecture Decision

The LLM generates standard YAML. We chose this approach because YAML is well-represented in LLM training data, easy to prompt for, and structured enough to parse reliably.

The flow is:

```
YAML string (LLM output)
        |
  yaml.safe_load()          # PyYAML -- string to Python dict
        |
  validate_structure()      # checks required fields and basic types
        |
  validate_vocabulary()     # checks every op is in the 25 VALID_OPS
        |
  build_ast()               # constructs typed WorkflowAST
        |
  WorkflowAST               # what the type_checker and taint_analyser consume
```

At each step, failures return structured error messages -- not raw exceptions. This is critical because those errors go directly into the LLM repair prompt inside the synthesis loop.

**Note on Lark:** the skill specifies "Python + Lark" for the parser. In this session, structure and vocabulary validation are done in plain Python -- it is more direct, easier to debug, and sufficient for the system's needs. Lark is kept as an available dependency and can be added as a pre-parse validation layer if LLM input quality issues arise later. We do not introduce it now to avoid complexity before we have evidence we need it.

---

## YAML Format the LLM Must Generate

The LLM must produce workflows in the following format:

```yaml
workflow_id: invoice_approval_workflow
steps:
  - id: step_fetch
    op: fetch_api
    params:
      endpoint: "/api/invoices/pending"
    output: raw_invoices

  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices

  - id: step_auth
    op: authenticate_user
    params:
      input: validated_invoices
      role: "approver"
    output: auth_result

  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result
```

Required workflow fields: `workflow_id`, `steps`.
Required per step: `id`, `op`.
Optional per step: `params`, `output`.

---

## File 1: `src/dsl/constants.py`

This file is the single source of truth for the DSL vocabulary. The parser, type checker, and taint analyser all import from here. If a primitive ever changes, it changes in one place.

```python
# src/dsl/constants.py
#
# Official WorkflowSynth DSL vocabulary.
# These 25 operators are the only permitted vocabulary.
# No component may accept an op that is not listed here.
#
# CONSTRAINT: changing this vocabulary requires updating type_checker.py,
# taint.py, and all Dataset A test suites. Log it in the Implementation Journal.

# --- The 25 valid operators ---------------------------------------------------

VALID_OPS: set[str] = {
    # Data Operations (8)
    "fetch_api",
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",

    # Control Flow (8)
    "route_to_step",
    "apply_rule",
    "loop_records",
    "parallel_execute",
    "wait_for_condition",
    "handle_error",
    "retry_step",
    "terminate_workflow",

    # Integration Operations (9)
    "send_to_queue",
    "log_audit",
    "notify_user",
    "call_webhook",
    "read_database",
    "write_database",
    "authenticate_user",
    "encrypt_field",
    "call_subworkflow",
}

# --- Output type signatures ---------------------------------------------------
#
# Each operator declares an output type.
# The type checker uses this to validate that the output of one step
# is compatible with the input of the step that consumes it.
#
# Possible types:
#   "records"    -- list of records (list of dicts)
#   "record"     -- a single record (dict)
#   "boolean"    -- True / False
#   "string"     -- text
#   "any"        -- flexible output (type checking is permissive)
#   "none"       -- no output produced (side-effect only)
#   "auth_token" -- result of authenticate_user; required before write ops

OP_OUTPUT_TYPES: dict[str, str] = {
    # Data Operations
    "fetch_api":       "records",
    "filter_records":  "records",
    "transform_json":  "records",
    "validate_schema": "records",
    "aggregate_data":  "record",
    "merge_datasets":  "records",
    "extract_field":   "any",
    "format_output":   "string",

    # Control Flow
    "route_to_step":      "none",
    "apply_rule":         "boolean",
    "loop_records":       "none",
    "parallel_execute":   "none",
    "wait_for_condition": "none",
    "handle_error":       "none",
    "retry_step":         "none",
    "terminate_workflow": "none",

    # Integration Operations
    "send_to_queue":     "none",
    "log_audit":         "none",
    "notify_user":       "none",
    "call_webhook":      "any",
    "read_database":     "records",
    "write_database":    "none",
    "authenticate_user": "auth_token",
    "encrypt_field":     "string",
    "call_subworkflow":  "any",
}

# --- Operators that require an input param ------------------------------------
#
# These operators must have params.input declared.
# The type checker verifies that the referenced input exists as the output
# of a previous step.

OPS_REQUIRING_INPUT: set[str] = {
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",
    "write_database",
    "send_to_queue",
    "call_webhook",
    "notify_user",
    "encrypt_field",
}

# --- Security rule: authenticate_user must precede these ops -----------------
#
# CONSTRAINT (Architectural Decision 3):
# Any step using these operators must have a preceding authenticate_user step.
# This rule is enforced in the type checker, not the taint analyser.

OPS_REQUIRING_AUTH: set[str] = {
    "write_database",
    "call_webhook",
}
```

---

## File 2: `src/dsl/ast_nodes.py`

The internal workflow representation. Once the parser builds a `WorkflowAST`, every other system component works with this object -- never with raw dicts.

```python
# src/dsl/ast_nodes.py
#
# Internal representation of a WorkflowSynth workflow.
# The parser converts YAML -> WorkflowAST.
# The type_checker and taint_analyser operate on WorkflowAST.
# The adapters (n8n, LangChain) take WorkflowAST as input.

from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    """
    A single step in the workflow.

    Fields:
        id:     unique identifier for this step within the workflow.
                Generated by the LLM. Validated by the parser as a non-empty string.
        op:     DSL operator. Must be in VALID_OPS.
                The parser rejects any value outside the vocabulary.
        params: step parameters. Free dict -- each operator has its own semantics.
                The type checker validates critical fields (input, schema, etc.)
                according to the operator.
        output: name of the variable this step produces.
                Other steps can reference this name in params.input.
                May be None if the step produces no output.
    """
    id: str
    op: str
    params: dict = field(default_factory=dict)
    output: str | None = None


@dataclass
class WorkflowAST:
    """
    Complete representation of a WorkflowSynth workflow.

    Fields:
        workflow_id: unique identifier for the workflow.
        steps:       ordered list of WorkflowStep.
                     Order matters -- it defines the execution sequence.
    """
    workflow_id: str
    steps: list[WorkflowStep] = field(default_factory=list)

    def step_ids(self) -> list[str]:
        """Returns the IDs of all steps, in order."""
        return [s.id for s in self.steps]

    def output_vars(self) -> dict[str, str]:
        """
        Returns a map of output_var -> op for all steps that declare an output.
        Useful for the type_checker when verifying that params.input
        references an existing output.
        """
        return {
            s.output: s.op
            for s in self.steps
            if s.output is not None
        }
```

---

## File 3: `src/dsl/parser.py`

The parser is the core of the DSL Layer. It takes the YAML string generated by the LLM and converts it into a validated `WorkflowAST`, or returns a list of structured errors.

The main function is `parse_workflow()`. It calls three validation functions in sequence. If any step fails, it returns the errors immediately -- there is no point building an AST on an invalid structure.

```python
# src/dsl/parser.py
#
# Main parser for the WorkflowSynth DSL.
# Converts a YAML string (LLM output) into a typed WorkflowAST.
#
# Usage:
#   from workflowsynth.dsl.parser import parse_workflow
#   result = parse_workflow(yaml_string)
#   if result["ok"]:
#       ast = result["ast"]
#   else:
#       errors = result["errors"]  # list of strings for the repair prompt

import yaml
from .ast_nodes import WorkflowAST, WorkflowStep
from .constants import VALID_OPS


def parse_workflow(yaml_string: str) -> dict:
    """
    Parses an LLM-generated YAML string and returns a WorkflowAST.

    Returns a dict with the following structure:
        { "ok": True,  "ast": WorkflowAST }       -- success
        { "ok": False, "errors": list[str] }       -- failure with errors

    Errors are written to be useful in a repair prompt:
    they are descriptive, reference the problematic step,
    and suggest the correction.
    """

    # Step 1: parse YAML
    parse_result = _parse_yaml(yaml_string)
    if not parse_result["ok"]:
        return parse_result

    raw = parse_result["data"]

    # Step 2: validate structure (required fields, basic types)
    struct_errors = _validate_structure(raw)
    if struct_errors:
        return {"ok": False, "errors": struct_errors}

    # Step 3: validate vocabulary (ops must be in VALID_OPS)
    vocab_errors = _validate_vocabulary(raw)
    if vocab_errors:
        return {"ok": False, "errors": vocab_errors}

    # Step 4: build the AST
    ast = _build_ast(raw)
    return {"ok": True, "ast": ast}


# --- Step 1: YAML parsing ----------------------------------------------------

def _parse_yaml(yaml_string: str) -> dict:
    """
    Converts a YAML string to a Python dict.
    Uses yaml.safe_load() -- never yaml.load() as it executes arbitrary code.
    """
    try:
        data = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        return {
            "ok": False,
            "errors": [f"YAML syntax error: {str(e)}. "
                       "The workflow must be valid YAML."]
        }

    if not isinstance(data, dict):
        return {
            "ok": False,
            "errors": ["The YAML must parse to a dict at the top level. "
                       "Expected keys: workflow_id, steps."]
        }

    return {"ok": True, "data": data}


# --- Step 2: structure validation --------------------------------------------

def _validate_structure(raw: dict) -> list[str]:
    """
    Verifies the dict has required fields and correct types.
    Returns a list of errors (empty if all is well).
    """
    errors = []

    # workflow_id: required, non-empty string
    if "workflow_id" not in raw:
        errors.append("Missing required field 'workflow_id'.")
    elif not isinstance(raw["workflow_id"], str) or not raw["workflow_id"].strip():
        errors.append("Field 'workflow_id' must be a non-empty string.")

    # steps: required, non-empty list
    if "steps" not in raw:
        errors.append("Missing required field 'steps'.")
        return errors  # cannot validate further without steps
    if not isinstance(raw["steps"], list):
        errors.append("Field 'steps' must be a list.")
        return errors
    if len(raw["steps"]) == 0:
        errors.append("Field 'steps' must not be empty.")
        return errors

    # validate each step
    seen_ids: set[str] = set()
    for i, step in enumerate(raw["steps"]):
        step_errors = _validate_step(step, i, seen_ids)
        errors.extend(step_errors)

    return errors


def _validate_step(step: dict, index: int, seen_ids: set[str]) -> list[str]:
    """Validates the structure of a single step."""
    errors = []
    prefix = f"Step at index {index}"

    if not isinstance(step, dict):
        errors.append(f"{prefix}: must be a dict, got {type(step).__name__}.")
        return errors

    # id: required, unique, non-empty string
    if "id" not in step:
        errors.append(f"{prefix}: missing required field 'id'.")
    elif not isinstance(step["id"], str) or not step["id"].strip():
        errors.append(f"{prefix}: 'id' must be a non-empty string.")
    elif step["id"] in seen_ids:
        errors.append(f"{prefix}: duplicate step id '{step['id']}'. "
                      "Step IDs must be unique within the workflow.")
    else:
        seen_ids.add(step["id"])

    # op: required, string (vocabulary checked in _validate_vocabulary)
    if "op" not in step:
        errors.append(f"{prefix} (id='{step.get('id', '?')}'): "
                      "missing required field 'op'.")
    elif not isinstance(step["op"], str):
        errors.append(f"{prefix} (id='{step.get('id', '?')}'): "
                      "'op' must be a string.")

    # params: optional, but must be a dict if present
    if "params" in step and not isinstance(step["params"], dict):
        errors.append(f"{prefix} (id='{step.get('id', '?')}'): "
                      "'params' must be a dict if present.")

    # output: optional, but must be a string if present
    if "output" in step and not isinstance(step["output"], str):
        errors.append(f"{prefix} (id='{step.get('id', '?')}'): "
                      "'output' must be a string if present.")

    return errors


# --- Step 3: vocabulary validation -------------------------------------------

def _validate_vocabulary(raw: dict) -> list[str]:
    """
    Verifies every op is in VALID_OPS.
    Invalid ops are the most common LLM error.
    """
    errors = []
    for step in raw.get("steps", []):
        op = step.get("op", "")
        if isinstance(op, str) and op not in VALID_OPS:
            errors.append(
                f"Step '{step.get('id', '?')}': unknown op '{op}'. "
                f"Valid ops are: {sorted(VALID_OPS)}. "
                "Use only operations from the WorkflowSynth DSL vocabulary."
            )
    return errors


# --- Step 4: AST construction ------------------------------------------------

def _build_ast(raw: dict) -> WorkflowAST:
    """
    Constructs the WorkflowAST from the validated dict.
    At this point structure and vocabulary are guaranteed correct.
    """
    steps = []
    for step_dict in raw["steps"]:
        steps.append(WorkflowStep(
            id=step_dict["id"],
            op=step_dict["op"],
            params=step_dict.get("params", {}),
            output=step_dict.get("output"),
        ))

    return WorkflowAST(
        workflow_id=raw["workflow_id"],
        steps=steps,
    )
```

---

## File 4: `src/dsl/type_checker.py`

The type checker operates on the `WorkflowAST`. It verifies two things:

1. **Type flow:** when a step references `params.input`, that name must exist as the `output` of a previous step, and the output type must be compatible with what the operator expects.
2. **Authentication rule:** any `write_database` or `call_webhook` must have a preceding `authenticate_user` step in the workflow.

```python
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
```

---

## File 5: `src/dsl/__init__.py`

```python
# src/dsl/__init__.py
# Public interface of the DSL Layer.

from .parser import parse_workflow
from .type_checker import type_check
from .ast_nodes import WorkflowAST, WorkflowStep
from .constants import VALID_OPS, OP_OUTPUT_TYPES

__all__ = [
    "parse_workflow",
    "type_check",
    "WorkflowAST",
    "WorkflowStep",
    "VALID_OPS",
    "OP_OUTPUT_TYPES",
]
```

---

## Tests

### `tests/unit/test_parser.py`

```python
# tests/unit/test_parser.py

import pytest
from workflowsynth.dsl.parser import parse_workflow


# --- Valid YAML --------------------------------------------------------------

VALID_YAML_MINIMAL = """
workflow_id: test_workflow
steps:
  - id: step_1
    op: fetch_api
    params:
      endpoint: "/data"
    output: raw_data
"""

def test_valid_minimal_workflow():
    result = parse_workflow(VALID_YAML_MINIMAL)
    assert result["ok"] is True
    ast = result["ast"]
    assert ast.workflow_id == "test_workflow"
    assert len(ast.steps) == 1
    assert ast.steps[0].id == "step_1"
    assert ast.steps[0].op == "fetch_api"
    assert ast.steps[0].output == "raw_data"


VALID_YAML_FULL = """
workflow_id: invoice_approval
steps:
  - id: step_fetch
    op: fetch_api
    params:
      endpoint: "/api/invoices"
    output: raw_invoices
  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated
  - id: step_auth
    op: authenticate_user
    params:
      role: "approver"
    output: auth_token
  - id: step_write
    op: write_database
    params:
      input: validated
      table: invoices
"""

def test_valid_full_workflow():
    result = parse_workflow(VALID_YAML_FULL)
    assert result["ok"] is True
    assert len(result["ast"].steps) == 4


# --- YAML errors -------------------------------------------------------------

def test_invalid_yaml_syntax():
    result = parse_workflow("workflow_id: test\nsteps: [unclosed")
    assert result["ok"] is False
    assert any("YAML syntax error" in e for e in result["errors"])

def test_yaml_not_a_dict():
    result = parse_workflow("- just a list")
    assert result["ok"] is False
    assert any("dict" in e for e in result["errors"])


# --- Structure errors --------------------------------------------------------

def test_missing_workflow_id():
    result = parse_workflow("steps:\n  - id: s1\n    op: fetch_api")
    assert result["ok"] is False
    assert any("workflow_id" in e for e in result["errors"])

def test_missing_steps():
    result = parse_workflow("workflow_id: test")
    assert result["ok"] is False
    assert any("steps" in e for e in result["errors"])

def test_empty_steps():
    result = parse_workflow("workflow_id: test\nsteps: []")
    assert result["ok"] is False
    assert any("empty" in e for e in result["errors"])

def test_step_missing_id():
    result = parse_workflow("workflow_id: t\nsteps:\n  - op: fetch_api")
    assert result["ok"] is False
    assert any("'id'" in e for e in result["errors"])

def test_step_missing_op():
    result = parse_workflow("workflow_id: t\nsteps:\n  - id: s1")
    assert result["ok"] is False
    assert any("'op'" in e for e in result["errors"])

def test_duplicate_step_ids():
    yaml = """
workflow_id: t
steps:
  - id: step_1
    op: fetch_api
  - id: step_1
    op: filter_records
"""
    result = parse_workflow(yaml)
    assert result["ok"] is False
    assert any("duplicate" in e for e in result["errors"])


# --- Vocabulary errors -------------------------------------------------------

def test_invalid_op():
    yaml = "workflow_id: t\nsteps:\n  - id: s1\n    op: send_email\n"
    result = parse_workflow(yaml)
    assert result["ok"] is False
    assert any("send_email" in e for e in result["errors"])
    assert any("unknown op" in e for e in result["errors"])

def test_all_valid_ops_accepted():
    """Verifies all 25 vocabulary ops are accepted by the parser."""
    from workflowsynth.dsl.constants import VALID_OPS
    for op in VALID_OPS:
        yaml = f"workflow_id: t\nsteps:\n  - id: s1\n    op: {op}\n"
        result = parse_workflow(yaml)
        vocab_errors = [e for e in result.get("errors", []) if "unknown op" in e]
        assert len(vocab_errors) == 0, f"Op '{op}' was incorrectly rejected: {vocab_errors}"
```

### `tests/unit/test_type_checker.py`

```python
# tests/unit/test_type_checker.py

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.dsl.type_checker import type_check


def _parse_and_check(yaml_string: str) -> list[str]:
    """Helper: parses YAML and runs the type checker. Returns errors."""
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed unexpectedly: {result.get('errors')}"
    return type_check(result["ast"])


# --- Valid workflows ---------------------------------------------------------

def test_valid_type_flow():
    """fetch_api -> validate_schema: records -> records. Should pass."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/data"
    output: raw_data
  - id: s2
    op: validate_schema
    params:
      input: raw_data
      schema: my_schema
    output: clean_data
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: clean_data
      table: my_table
"""
    errors = _parse_and_check(yaml)
    assert errors == []


# --- Input errors ------------------------------------------------------------

def test_missing_input_param():
    """validate_schema without params.input should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: validate_schema
    params:
      schema: my_schema
"""
    errors = _parse_and_check(yaml)
    assert any("missing required param 'input'" in e for e in errors)


def test_input_references_undefined_var():
    """Referencing an output that does not exist should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: filter_records
    params:
      input: nonexistent_var
"""
    errors = _parse_and_check(yaml)
    assert any("not defined" in e for e in errors)


def test_input_references_later_step():
    """Cannot reference the output of a step that comes after."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: filter_records
    params:
      input: data_from_s2
  - id: s2
    op: fetch_api
    output: data_from_s2
"""
    errors = _parse_and_check(yaml)
    assert any("not defined" in e for e in errors)


# --- Type mismatch errors ----------------------------------------------------

def test_type_mismatch_string_into_records_op():
    """
    encrypt_field outputs 'string'.
    filter_records requires 'records'.
    Should produce a type error.
    """
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
    output: encrypted_value
  - id: s3
    op: filter_records
    params:
      input: encrypted_value
"""
    errors = _parse_and_check(yaml)
    assert any("type" in e.lower() for e in errors)


# --- Authentication rule errors ----------------------------------------------

def test_write_database_without_auth():
    """write_database without a preceding authenticate_user should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: write_database
    params:
      input: data
      table: t
"""
    errors = _parse_and_check(yaml)
    assert any("authenticate_user" in e for e in errors)
    assert any("write_database" in e for e in errors)


def test_call_webhook_without_auth():
    """call_webhook without a preceding authenticate_user should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: call_webhook
    params:
      input: data
      url: "https://example.com"
"""
    errors = _parse_and_check(yaml)
    assert any("authenticate_user" in e for e in errors)


def test_write_database_with_auth_passes():
    """write_database with a preceding authenticate_user should pass."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      input: data
      table: my_table
"""
    errors = _parse_and_check(yaml)
    auth_errors = [e for e in errors if "authenticate_user" in e]
    assert auth_errors == []
```

---

## File structure to create in the repo

```
workflowsynth/
  src/
    dsl/
      __init__.py
      constants.py
      ast_nodes.py
      parser.py
      type_checker.py
  tests/
    unit/
      test_parser.py
      test_type_checker.py
```

---

## Dependencies

Add to `pyproject.toml` or `requirements.txt`:

```
pyyaml>=6.0
lark>=1.2       # available for future use
pytest>=8.0
```

---

## How to run the tests

```bash
# from the repo root
pip install -e .
pytest tests/unit/ -v
```

---

## Implementation Journal

```
Date: 2026-08-06
DSR Phase: Build
Component: DSL Layer
Type: Decision
Description: DSL Layer architecture defined. Parser based on PyYAML with
  plain Python validation in three sequential steps (structure, vocabulary, AST).
  Lark kept as an available dependency but not used in this sprint.
Justification: PyYAML + plain Python is more direct, easier to debug,
  and sufficient. Lark adds complexity without clear benefit until
  concrete LLM input quality problems arise that require formal grammar.
Dissertation Impact: Architectural Decision 1 (Two-Layer DSL Design).
  Implementation section of the Specification and Design Report.
```

```
Date: 2026-08-06
DSR Phase: Build
Component: DSL Layer -- Type Checker
Type: Decision
Description: The authentication rule (authenticate_user must precede
  write_database and call_webhook) is enforced as precedence in the
  workflow, not as a direct output-to-input connection.
Justification: Requiring a direct connection would be overly restrictive
  for workflows with multiple branches. Precedence captures the security
  intent without blocking legitimate enterprise workflow patterns.
Dissertation Impact: Architectural Decision 3 (Two-Stage Verification).
  Security verification section.
```

---

## Next Session

Session 02 -- Taint Analysis Engine (`src/verification/taint.py`).

The core logic is already specified in the skill (taint_sources, taint_sinks, sanitisers). The next session implements it formally, adds tests, and integrates it with the parser to complete Stage 1 verification.
