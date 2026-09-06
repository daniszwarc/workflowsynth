# Test suite for wf_mm_005: Clinical Data Verification
# Domain: clinical_ai | Complexity: 3

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


def test_extracts_from_both_sources(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    extract_ops = [s for s in ast.steps if s.op == "extract_field"]
    assert len(extract_ops) >= 2, "Must extract values from both source and output"

def test_assigns_confidence(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    rule_ops = [s for s in ast.steps if s.op == "apply_rule"]
    assert len(rule_ops) >= 2, "Must apply diff check and confidence rules"
