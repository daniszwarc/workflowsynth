# Test suite for wf_aw_001: User Login with Two-Factor Authentication
# Domain: enterprise_knowledge | Complexity: 3

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


def test_applies_rate_limiting(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "apply_rule" in [s.op for s in ast.steps]

def test_validates_2fa(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "validate_schema" in [s.op for s in ast.steps]
