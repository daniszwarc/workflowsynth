# tests/unit/test_pipeline.py
#
# Unit tests for the LangGraph pipeline nodes and routing logic.
#
# NOTE: These tests do NOT invoke the full compiled pipeline (that requires
# LLM API keys). Instead, they test each node in isolation and test the
# routing logic of check_pass_or_repair directly.
# Integration tests with the full pipeline are in tests/integration/.

import pytest
from unittest.mock import patch, MagicMock
from workflowsynth.synthesis.state import WorkflowSynthState, initial_state
from workflowsynth.synthesis.nodes import (
    verify_dsl,
    run_tests,
    check_pass_or_repair,
    repair_with_llm,
    record_failure,
    classify_failure,
    select_model,
)


# --- initial_state -----------------------------------------------------------

def test_initial_state_defaults():
    state = initial_state("When an invoice arrives, validate and store it.")
    assert state["natural_language_spec"] == "When an invoice arrives, validate and store it."
    assert state["repair_attempt"] == 0
    assert state["max_attempts"] == 10
    assert state["attempt_history"] == []
    assert state["synthesis_successful"] is False
    assert state["final_n8n_json"] is None
    assert state["final_langchain_python"] is None


# --- verify_dsl node ---------------------------------------------------------

VALID_YAML = """
workflow_id: test_wf
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: /data
    output: raw
  - id: s2
    op: validate_schema
    params:
      input: raw
      schema: s
    output: clean
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: clean
      table: t
"""

INVALID_YAML = "not: valid: yaml: ["

TAINT_VIOLATION_YAML = """
workflow_id: test_wf
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: write_database
    params:
      input: raw
      table: t
"""

def test_verify_dsl_valid_workflow():
    state = initial_state("test")
    state["llm_sketch"] = VALID_YAML
    result = verify_dsl(state)
    assert result["dsl_verification_passed"] is True
    assert result["dsl_type_errors"] == []
    assert result["dsl_taint_violations"] == []
    assert result["dsl_candidate"]["workflow_id"] == "test_wf"

def test_verify_dsl_invalid_yaml():
    state = initial_state("test")
    state["llm_sketch"] = INVALID_YAML
    result = verify_dsl(state)
    assert result["dsl_verification_passed"] is False
    assert len(result["dsl_type_errors"]) > 0
    assert result["dsl_candidate"] == {}

def test_verify_dsl_taint_violation():
    state = initial_state("test")
    state["llm_sketch"] = TAINT_VIOLATION_YAML
    result = verify_dsl(state)
    assert result["dsl_verification_passed"] is False
    assert len(result["dsl_taint_violations"]) > 0

def test_verify_dsl_stores_candidate_as_dict():
    state = initial_state("test")
    state["llm_sketch"] = VALID_YAML
    result = verify_dsl(state)
    assert isinstance(result["dsl_candidate"], dict)
    assert "steps" in result["dsl_candidate"]
    assert all(isinstance(s, dict) for s in result["dsl_candidate"]["steps"])


# --- run_tests node ----------------------------------------------------------

def test_run_tests_skips_if_verification_failed():
    state = initial_state("test")
    state["dsl_verification_passed"] = False
    result = run_tests(state)
    assert result["test_results"] == {}

def test_run_tests_runs_if_verification_passed():
    state = initial_state("test")
    state["dsl_verification_passed"] = True
    result = run_tests(state)
    # Stub returns a passing result
    assert result["test_results"] != {}
    assert all(result["test_results"].values())


# --- check_pass_or_repair routing --------------------------------------------

def test_routing_pass_when_verified_and_tests_pass():
    state = initial_state("test")
    state["dsl_verification_passed"] = True
    state["test_results"] = {"test_1": True, "test_2": True}
    state["repair_attempt"] = 0
    assert check_pass_or_repair(state) == "pass"

def test_routing_repair_when_verification_fails_and_attempts_remain():
    state = initial_state("test")
    state["dsl_verification_passed"] = False
    state["test_results"] = {}
    state["repair_attempt"] = 3
    state["max_attempts"] = 10
    assert check_pass_or_repair(state) == "repair"

def test_routing_record_failure_when_attempts_exhausted():
    state = initial_state("test")
    state["dsl_verification_passed"] = False
    state["test_results"] = {}
    state["repair_attempt"] = 9        # last attempt (0-indexed, max=10)
    state["max_attempts"] = 10
    assert check_pass_or_repair(state) == "record_failure"

def test_routing_repair_when_tests_fail_and_attempts_remain():
    state = initial_state("test")
    state["dsl_verification_passed"] = True
    state["test_results"] = {"test_1": True, "test_2": False}
    state["repair_attempt"] = 2
    state["max_attempts"] = 10
    assert check_pass_or_repair(state) == "repair"


# --- repair_with_llm node ----------------------------------------------------

@patch("workflowsynth.synthesis.nodes.get_llm")
def test_repair_appends_to_history(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        "workflow_id: stub\nsteps:\n  - id: s1\n    op: fetch_api\n"
    )
    mock_get_llm.return_value = mock_llm

    state = initial_state("test")
    state["llm_sketch"] = VALID_YAML
    state["dsl_type_errors"] = ["some error"]
    state["dsl_taint_violations"] = []
    state["test_results"] = {}
    state["repair_attempt"] = 0
    state["attempt_history"] = []

    result = repair_with_llm(state)

    assert len(result["attempt_history"]) == 1
    assert result["attempt_history"][0]["attempt_number"] == 0
    assert result["repair_attempt"] == 1

@patch("workflowsynth.synthesis.nodes.get_llm")
def test_repair_history_is_append_only(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        "workflow_id: stub\nsteps:\n  - id: s1\n    op: fetch_api\n"
    )
    mock_get_llm.return_value = mock_llm

    state = initial_state("test")
    state["llm_sketch"] = VALID_YAML
    state["dsl_type_errors"] = []
    state["dsl_taint_violations"] = []
    state["test_results"] = {"t": False}
    state["repair_attempt"] = 2
    state["attempt_history"] = [{"attempt_number": 0}, {"attempt_number": 1}]

    result = repair_with_llm(state)

    assert len(result["attempt_history"]) == 3
    assert result["attempt_history"][0]["attempt_number"] == 0
    assert result["attempt_history"][1]["attempt_number"] == 1
    assert result["attempt_history"][2]["attempt_number"] == 2


# --- record_failure node -----------------------------------------------------

def test_record_failure_sets_synthesis_unsuccessful():
    state = initial_state("test")
    state["attempt_history"] = [
        {"attempt_number": i, "dsl_type_errors": ["err"], "dsl_taint_violations": [],
         "test_results": {}, "failure_category": "type_error"}
        for i in range(10)
    ]
    result = record_failure(state)
    assert result["synthesis_successful"] is False
    assert result["failure_category"] == "type_error"

def test_record_failure_with_empty_history():
    state = initial_state("test")
    state["attempt_history"] = []
    result = record_failure(state)
    assert result["synthesis_successful"] is False
    assert result["failure_category"] == "max_attempts_exceeded"


# --- classify_failure --------------------------------------------------------

def test_classify_failure_most_common_category():
    history = [
        {"failure_category": "type_error"},
        {"failure_category": "type_error"},
        {"failure_category": "taint_violation"},
    ]
    assert classify_failure(history) == "type_error"

def test_classify_failure_empty_history():
    assert classify_failure([]) == "max_attempts_exceeded"


# --- select_model ------------------------------------------------------------

def test_select_model_claude_for_early_attempts():
    for i in range(8):
        assert select_model(i) == "claude-opus-4-6"

def test_select_model_gpt_for_late_attempts():
    assert select_model(8) == "gpt-5.4-2026-03-05"
    assert select_model(9) == "gpt-5.4-2026-03-05"
