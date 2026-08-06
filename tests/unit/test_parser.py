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
