# Test suite for wf_ae_006: Full Article Publishing Pipeline
# Domain: publishing | Complexity: 4

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


def test_sanitises_before_publish(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    violations = taint_analysis(ast)
    assert violations == [], f"Taint violations: {[v.message for v in violations]}"

def test_auth_before_write(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    auth_idx = next((i for i, o in enumerate(ops) if o == "authenticate_user"), None)
    webhook_indices = [i for i, o in enumerate(ops) if o == "call_webhook"]
    cms_write_idx = max(webhook_indices) if webhook_indices else None
    assert auth_idx is not None and cms_write_idx is not None
    assert auth_idx < cms_write_idx

def test_has_audit_log(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "log_audit" in [s.op for s in ast.steps]
