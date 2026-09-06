# Test suite for wf_btp_005: Lab Trend Time Series Load
# Domain: clinical_ai | Complexity: 2

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


def test_filters_translation_files(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    read_ops = [s for s in ast.steps if s.op == "read_database"]
    assert len(read_ops) >= 1, "Must read lab history"

def test_formats_time_series(candidate_yaml):
    ast = load_candidate(candidate_yaml)
    assert "format_output" in [s.op for s in ast.steps]
