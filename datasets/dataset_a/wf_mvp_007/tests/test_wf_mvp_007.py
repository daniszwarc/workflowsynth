# Test suite for wf_mvp_007: Approve Invoice and Upload Payment
# Domain: manufacturing | Complexity: 4

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


def test_writes_to_both_databases(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    write_ops = [s for s in ast.steps if s.op=="write_database"]
    assert len(write_ops) >= 3, "Must write to legacy, new service, and history tables"
