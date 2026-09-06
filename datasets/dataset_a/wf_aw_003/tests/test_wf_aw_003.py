# Test suite for wf_aw_003: Business Rule Extraction from Process Document
# Domain: enterprise_knowledge | Complexity: 4

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


def test_stores_pending_review(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "write_database" in [s.op for s in ast.steps]

def test_generates_embeddings(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    webhook_calls = [s for s in ast.steps if s.op=="call_webhook"]
    assert len(webhook_calls) >= 2, "Must call LLM for extraction and embeddings"
