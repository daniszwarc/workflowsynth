# tests/unit/test_prompts.py
#
# Tests for WorkflowSynth prompt construction.
# No API keys required -- tests prompt content and structure only.

import pytest
from workflowsynth.synthesis.prompts import SYSTEM_PROMPT, build_repair_prompt
from workflowsynth.dsl.constants import VALID_OPS


# --- System prompt -----------------------------------------------------------

def test_system_prompt_contains_all_25_ops():
    """All 25 VALID_OPS must appear in the system prompt."""
    missing = [op for op in VALID_OPS if op not in SYSTEM_PROMPT]
    assert missing == [], f"Ops missing from system prompt: {missing}"

def test_system_prompt_contains_hard_constraints():
    """Key constraint keywords must appear in the system prompt."""
    assert "authenticate_user" in SYSTEM_PROMPT
    assert "write_database" in SYSTEM_PROMPT
    assert "untrusted" in SYSTEM_PROMPT
    assert "ONLY valid YAML" in SYSTEM_PROMPT

def test_system_prompt_contains_example():
    """The system prompt must contain a concrete YAML example."""
    assert "workflow_id:" in SYSTEM_PROMPT
    assert "steps:" in SYSTEM_PROMPT
    assert "op:" in SYSTEM_PROMPT

def test_system_prompt_no_markdown_fences():
    """
    The system prompt must not contain markdown code fences (```).
    The example YAML must be raw, not wrapped in fences -- otherwise
    the LLM may mirror this format and wrap its own output in fences,
    breaking the parser.
    """
    assert "```" not in SYSTEM_PROMPT


# --- Repair prompt -----------------------------------------------------------

def test_repair_prompt_includes_original_spec():
    prompt = build_repair_prompt(
        original_spec="When an invoice arrives, validate and store it.",
        failing_yaml="workflow_id: t\nsteps: []",
        type_errors=["Field 'steps' must not be empty."],
        taint_violations=[],
        test_failures={},
        attempt_number=0,
        max_attempts=10,
    )
    assert "When an invoice arrives, validate and store it." in prompt

def test_repair_prompt_includes_failing_yaml():
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="workflow_id: t\nsteps: []",
        type_errors=["some error"],
        taint_violations=[],
        test_failures={},
        attempt_number=1,
        max_attempts=10,
    )
    assert "workflow_id: t\nsteps: []" in prompt

def test_repair_prompt_includes_type_errors():
    errors = ["Step 's1': missing required param 'input'."]
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=errors,
        taint_violations=[],
        test_failures={},
        attempt_number=0,
        max_attempts=10,
    )
    assert errors[0] in prompt
    assert "Type / structure errors" in prompt

def test_repair_prompt_includes_taint_violations():
    violations = ["Step 's2': tainted variable 'raw' reached a sink."]
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=[],
        taint_violations=violations,
        test_failures={},
        attempt_number=0,
        max_attempts=10,
    )
    assert violations[0] in prompt
    assert "Security violations" in prompt

def test_repair_prompt_includes_attempt_count():
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=["err"],
        taint_violations=[],
        test_failures={},
        attempt_number=3,
        max_attempts=10,
    )
    assert "4 of 10" in prompt  # attempt_number + 1

def test_repair_prompt_no_section_for_empty_errors():
    """If there are no taint violations, that section must not appear."""
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=["one type error"],
        taint_violations=[],
        test_failures={},
        attempt_number=0,
        max_attempts=10,
    )
    assert "Security violations" not in prompt

def test_repair_prompt_ends_with_yaml_instruction():
    """Repair prompt must always end with the YAML-only instruction."""
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=["err"],
        taint_violations=[],
        test_failures={},
        attempt_number=0,
        max_attempts=10,
    )
    assert prompt.strip().endswith("Respond with ONLY valid YAML. No prose, no markdown fences.")

def test_repair_prompt_includes_failed_tests_only():
    """Only failed tests appear in the repair prompt, not passing ones."""
    test_results = {"test_auth": True, "test_schema": False, "test_write": False}
    prompt = build_repair_prompt(
        original_spec="spec",
        failing_yaml="yaml",
        type_errors=[],
        taint_violations=[],
        test_failures=test_results,
        attempt_number=0,
        max_attempts=10,
    )
    assert "test_schema" in prompt
    assert "test_write" in prompt
    assert "test_auth" not in prompt
