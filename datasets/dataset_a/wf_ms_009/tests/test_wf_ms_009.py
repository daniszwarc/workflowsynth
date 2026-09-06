# Test suite for wf_ms_009: Full Clinical Analysis Pipeline
# Domain: clinical_ai | Complexity: 5

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


def test_anonymization_hard_gate(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    violations = taint_analysis(ast)
    assert violations == [], f"Taint violations: {[v.message for v in violations]}"

def test_encrypts_before_storage(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    enc_ops = [s for s in ast.steps if s.op=="encrypt_field"]
    assert len(enc_ops) >= 2

def test_has_audit_log(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "log_audit" in [s.op for s in ast.steps]
