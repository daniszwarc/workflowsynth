# Test suite for wf_pb_001: WhatsApp Text Message Ingestion
# Domain: insurance_brokerage | Complexity: 2

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.dsl.type_checker import type_check
from workflowsynth.verification.taint import taint_analysis


def load_candidate(yaml_string: str):
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parse failed: {result.get('errors')}"
    return result["ast"]


def test_parses_and_type_checks(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert type_check(ast) == []


def test_passes_taint_analysis(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    violations = taint_analysis(ast)
    assert violations == [], f"Taint violations: {[v.message for v in violations]}"


def test_has_sanitisation_before_ai_call(candidate_yaml):
    """Sensitive data must be masked before reaching the AI classification API."""
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    sanitiser_ops = {"validate_schema", "transform_json", "filter_records", "encrypt_field", "extract_field"}
    webhook_idx = next((i for i, s in enumerate(ast.steps) if s.op == "call_webhook"), None)
    if webhook_idx is not None:
        preceding_ops = set(ops[:webhook_idx])
        assert preceding_ops & sanitiser_ops, "A sanitiser must precede the AI classification call"

def test_has_ticket_creation(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    assert "write_database" in ops, "Must create a ticket in the database"

def test_has_classification_step(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    assert "call_webhook" in ops or "call_subworkflow" in ops, "Must call AI classification API"
