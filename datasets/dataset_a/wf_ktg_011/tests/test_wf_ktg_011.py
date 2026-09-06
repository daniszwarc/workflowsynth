# Test suite for wf_ktg_011: Email-to-Claim Ingestion Pipeline
# Domain: workers_compensation | Complexity: 4

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


def test_validates_before_creating_claim(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    val_indices = [i for i,o in enumerate(ops) if o=="validate_schema"]
    write_idx = next((i for i,o in enumerate(ops) if o=="write_database"),None)
    assert val_indices and write_idx
    assert max(val_indices) < write_idx, "All validation must precede claim creation"

def test_notifies_staff(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "notify_user" in [s.op for s in ast.steps]
