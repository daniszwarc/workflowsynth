# tests/unit/test_integration.py
#
# Unit tests for the n8n and LangChain integration adapters.

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.verification.evidence_report import generate_evidence_report
from workflowsynth.integration.n8n_adapter import to_n8n_json, to_n8n_json_string
from workflowsynth.integration.langchain_adapter import to_langchain_python


def _parse(yaml_string: str):
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed: {result.get('errors')}"
    return result["ast"]


def _report(ast):
    return generate_evidence_report(
        ast=ast,
        synthesis_attempts=1,
        type_errors=[],
        taint_violations=[],
        test_results={"stub_test": True},
    )


FULL_YAML = """
workflow_id: invoice_approval
steps:
  - id: fetch_invoices
    op: fetch_api
    params:
      endpoint: "/api/invoices"
    output: raw_invoices
  - id: validate_invoices
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices
  - id: authenticate_approver
    op: authenticate_user
    params:
      role: approver
    output: auth_result
  - id: store_invoices
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result
"""


# --- n8n adapter -------------------------------------------------------------

def test_n8n_output_has_required_top_level_keys():
    ast = _parse(FULL_YAML)
    report = _report(ast)
    result = to_n8n_json(ast, report)
    assert "name" in result
    assert "nodes" in result
    assert "connections" in result
    assert "meta" in result

def test_n8n_workflow_name_matches_workflow_id():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    assert result["name"] == "invoice_approval"

def test_n8n_has_one_node_per_step():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    assert len(result["nodes"]) == len(ast.steps)

def test_n8n_nodes_have_correct_ids():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    node_ids = [n["id"] for n in result["nodes"]]
    step_ids = [s.id for s in ast.steps]
    assert node_ids == step_ids

def test_n8n_nodes_have_valid_type():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    for node in result["nodes"]:
        assert "type" in node
        assert node["type"].startswith("n8n-nodes-base.")

def test_n8n_connections_link_sequential_steps():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    # First step should connect to second step
    first_step_id = ast.steps[0].id
    second_step_id = ast.steps[1].id
    assert first_step_id in result["connections"]
    connection = result["connections"][first_step_id]["main"][0][0]
    assert connection["node"] == second_step_id

def test_n8n_last_step_has_no_connection():
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    last_step_id = ast.steps[-1].id
    assert last_step_id not in result["connections"]

def test_n8n_active_is_false():
    """Workflow must not be active by default -- engineer must review first."""
    ast = _parse(FULL_YAML)
    result = to_n8n_json(ast, _report(ast))
    assert result["active"] is False

def test_n8n_meta_contains_evidence_report():
    ast = _parse(FULL_YAML)
    report = _report(ast)
    result = to_n8n_json(ast, report)
    assert "evidence_report" in result["meta"]
    er = result["meta"]["evidence_report"]
    assert "verified" in er
    assert "not_checked" in er
    assert "engineer_responsibilities" in er

def test_n8n_json_string_is_valid_json():
    import json
    ast = _parse(FULL_YAML)
    json_string = to_n8n_json_string(ast, _report(ast))
    parsed = json.loads(json_string)
    assert parsed["name"] == "invoice_approval"


# --- LangChain adapter -------------------------------------------------------

def test_langchain_output_is_string():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert isinstance(result, str)

def test_langchain_contains_evidence_report_docstring():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "EVIDENCE REPORT" in result
    assert "VERIFIED:" in result
    assert "NOT CHECKED:" in result
    assert "ENGINEER RESPONSIBILITIES" in result

def test_langchain_contains_run_workflow_function():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "def run_invoice_approval" in result

def test_langchain_contains_all_step_ids():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    for step in ast.steps:
        assert step.id in result

def test_langchain_contains_all_ops():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    for step in ast.steps:
        assert step.op in result

def test_langchain_imports_requests_when_fetch_api():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "import requests" in result

def test_langchain_imports_sqlalchemy_when_database_ops():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "sqlalchemy" in result

def test_langchain_imports_pydantic_when_validate_schema():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "pydantic" in result

def test_langchain_workflow_id_in_function_name():
    ast = _parse(FULL_YAML)
    result = to_langchain_python(ast, _report(ast))
    assert "invoice_approval" in result
