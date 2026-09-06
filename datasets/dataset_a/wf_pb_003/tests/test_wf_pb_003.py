# Test suite for wf_pb_003: Email Message Ingestion
# Domain: insurance_brokerage | Complexity: 3

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


def test_dedup_before_classification(candidate_yaml):
    """Deduplication must occur before AI classification."""
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    # processed_emails read (dedup) must come before call_webhook (classify)
    dedup_indices = [i for i, s in enumerate(ast.steps) if s.op == "read_database"]
    webhook_idx = next((i for i, s in enumerate(ast.steps) if s.op == "call_webhook"), None)
    assert dedup_indices and webhook_idx is not None
    assert min(dedup_indices) < webhook_idx, "Dedup read must precede classification"

def test_has_ticket_creation(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "write_database" in [s.op for s in ast.steps]
