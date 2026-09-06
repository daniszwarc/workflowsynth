# Test suite for wf_btp_003: RAG Clinical Chat
# Domain: clinical_ai | Complexity: 4

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


def test_validates_query_injection(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    val_idx = next((i for i,o in enumerate(ops) if o=="validate_schema"),None)
    webhook_idx = next((i for i,o in enumerate(ops) if o=="call_webhook"),None)
    assert val_idx < webhook_idx, "Must validate query before calling LLM"

def test_searches_both_stores(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    read_ops = [s for s in ast.steps if s.op == "read_database"]
    assert len(read_ops) >= 2, "Must search both raw and wiki vector stores"
