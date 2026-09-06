# Test suite for wf_ae_004: CMS Article Publication
# Domain: publishing | Complexity: 3

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


def test_csrf_before_post(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    fetch_idx = next((i for i, s in enumerate(ast.steps) if s.op == "fetch_api"), None)
    webhook_idx = next((i for i, s in enumerate(ast.steps) if s.op == "call_webhook"), None)
    assert fetch_idx is not None and webhook_idx is not None
    assert fetch_idx < webhook_idx, "CSRF token fetch must precede CMS POST"

def test_auth_before_publish(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    ops = [s.op for s in ast.steps]
    auth_idx = next((i for i, o in enumerate(ops) if o == "authenticate_user"), None)
    webhook_idx = next((i for i, o in enumerate(ops) if o == "call_webhook"), None)
    assert auth_idx < webhook_idx

def test_has_audit_log(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "log_audit" in [s.op for s in ast.steps]
