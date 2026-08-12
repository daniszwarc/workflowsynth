# tests/unit/test_evidence_report.py
#
# Unit tests for the evidence report generator.

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.verification.evidence_report import (
    generate_evidence_report,
    EvidenceReport,
)


def _parse(yaml_string: str):
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed: {result.get('errors')}"
    return result["ast"]


# --- Fixture workflows -------------------------------------------------------

FULL_WORKFLOW_YAML = """
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
    output: validated_invoices
  - id: step_auth
    op: authenticate_user
    params:
      role: approver
    output: auth_result
  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result
"""

SIMPLE_WORKFLOW_YAML = """
workflow_id: simple_log
steps:
  - id: step_log
    op: log_audit
    params:
      message: "workflow started"
"""

PARALLEL_WORKFLOW_YAML = """
workflow_id: parallel_wf
steps:
  - id: step_fetch
    op: fetch_api
    output: data
  - id: step_validate
    op: validate_schema
    params:
      input: data
      schema: s
    output: clean
  - id: step_parallel
    op: parallel_execute
  - id: step_auth
    op: authenticate_user
    params:
      role: admin
  - id: step_write
    op: write_database
    params:
      input: clean
      table: t
"""


# --- EvidenceReport generation -----------------------------------------------

def test_report_has_correct_workflow_id():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.workflow_id == "invoice_approval"

def test_report_has_generated_at_timestamp():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.generated_at is not None
    assert "2026" in report.generated_at  # UTC ISO format

def test_report_records_synthesis_attempts():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=3,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.synthesis_attempts == 3


# --- Verified claims ---------------------------------------------------------

def test_verified_contains_vocabulary_claim():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("vocabulary" in v.lower() for v in report.verified)

def test_verified_contains_type_safety_claim():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("type safety" in v.lower() for v in report.verified)

def test_verified_contains_auth_claim_when_write_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("authentication" in v.lower() for v in report.verified)

def test_verified_contains_taint_claim_when_sources_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("taint" in v.lower() for v in report.verified)

def test_verified_contains_test_results_when_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={"test_1": True, "test_2": True})
    assert any("test suite" in v.lower() or "2/2" in v for v in report.verified)

def test_no_auth_claim_when_no_write_or_webhook():
    """If no write_database or call_webhook, no auth claim is needed."""
    ast = _parse(SIMPLE_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert not any("authentication" in v.lower() for v in report.verified)


# --- Not checked section -----------------------------------------------------

def test_not_checked_always_has_business_logic():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("business logic" in n.lower() for n in report.not_checked)

def test_not_checked_has_rate_limits_when_external_calls():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("rate limit" in n.lower() for n in report.not_checked)

def test_not_checked_has_concurrency_when_parallel():
    ast = _parse(PARALLEL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("concurrency" in n.lower() for n in report.not_checked)

def test_not_checked_no_rate_limits_when_no_external():
    ast = _parse(SIMPLE_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert not any("rate limit" in n.lower() for n in report.not_checked)


# --- Engineer responsibilities ------------------------------------------------

def test_responsibilities_always_has_business_review():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("business" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_schema_review_when_validate_schema():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("schema" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_credentials_when_external():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("credential" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_db_review_when_write():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("write_database" in r.lower() or "data integrity" in r.lower()
               for r in report.engineer_responsibilities)


# --- to_dict and summary -----------------------------------------------------

def test_to_dict_has_required_keys():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    d = report.to_dict()
    assert "evidence_report" in d
    er = d["evidence_report"]
    assert "workflow_id" in er
    assert "generated_at" in er
    assert "verified" in er
    assert "not_checked" in er
    assert "engineer_responsibilities" in er

def test_summary_contains_all_sections():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=2,
                                      type_errors=[], taint_violations=[],
                                      test_results={"t1": True})
    summary = report.summary()
    assert "VERIFIED" in summary
    assert "NOT CHECKED" in summary
    assert "ENGINEER RESPONSIBILITIES" in summary
    assert "invoice_approval" in summary
    assert "2" in summary  # synthesis_attempts
