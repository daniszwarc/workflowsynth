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
