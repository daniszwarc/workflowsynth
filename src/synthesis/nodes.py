# src/synthesis/nodes.py
#
# The 8 LangGraph nodes of the WorkflowSynth synthesis pipeline.
# Each node takes WorkflowSynthState and returns a partial state update.
#
# LangGraph merges partial updates into the full state automatically --
# nodes only need to return the fields they modify.
#
# STUB NOTES (Session 03):
#   - translate_to_dsl and repair_with_llm stub the LLM call.
#     Real LLM integration is Session 04.
#   - translate_output and verify_output are stubs.
#     Real adapters are Session 06.

import subprocess
import tempfile
import json
from .state import WorkflowSynthState
from ..dsl.parser import parse_workflow
from ..dsl.type_checker import type_check
from ..verification.taint import taint_analysis


# --- Node 1: translate_to_dsl ------------------------------------------------

def translate_to_dsl(state: WorkflowSynthState) -> dict:
    """
    Calls the LLM to translate the natural language spec into a YAML DSL candidate.

    On the first attempt, the prompt contains only the spec.
    On subsequent attempts, the prompt also contains the attempt history
    so the LLM knows what errors it produced and what to fix.

    STUB: Returns a hardcoded minimal YAML for testing.
    Real LLM integration is Session 04.
    """
    # STUB: real implementation calls select_model() and the LangChain LLM client
    stub_yaml = (
        "workflow_id: stub_workflow\n"
        "steps:\n"
        "  - id: step_1\n"
        "    op: fetch_api\n"
        "    params:\n"
        "      endpoint: /data\n"
        "    output: raw_data\n"
    )
    return {"llm_sketch": stub_yaml}


# --- Node 2: verify_dsl ------------------------------------------------------

def verify_dsl(state: WorkflowSynthState) -> dict:
    """
    Stage 1 verification: parse_workflow + type_check + taint_analysis.

    Runs all three in sequence. Even if parsing fails, we do not raise --
    errors are recorded in state so check_pass_or_repair can decide next step.

    The parsed AST is stored as a dict in dsl_candidate for downstream nodes.
    If parsing fails, dsl_candidate is set to {} (empty dict).
    """
    yaml_string = state["llm_sketch"]
    type_errors: list[str] = []
    taint_violation_messages: list[str] = []
    dsl_candidate: dict = {}

    # Step 1: parse
    parse_result = parse_workflow(yaml_string)

    if not parse_result["ok"]:
        # Parsing failed -- record errors, mark verification as failed
        type_errors = parse_result["errors"]
        return {
            "dsl_candidate": {},
            "dsl_verification_passed": False,
            "dsl_type_errors": type_errors,
            "dsl_taint_violations": [],
        }

    ast = parse_result["ast"]

    # Step 2: type check
    type_errors = type_check(ast)

    # Step 3: taint analysis
    taint_violations = taint_analysis(ast)
    taint_violation_messages = [v.message for v in taint_violations]

    # Store the AST as a serialisable dict for downstream nodes
    # (LangGraph state must be JSON-serialisable)
    dsl_candidate = {
        "workflow_id": ast.workflow_id,
        "steps": [
            {
                "id": s.id,
                "op": s.op,
                "params": s.params,
                "output": s.output,
            }
            for s in ast.steps
        ],
    }

    passed = not type_errors and not taint_violation_messages

    return {
        "dsl_candidate": dsl_candidate,
        "dsl_verification_passed": passed,
        "dsl_type_errors": type_errors,
        "dsl_taint_violations": taint_violation_messages,
    }


# --- Node 3: run_tests -------------------------------------------------------

def run_tests(state: WorkflowSynthState) -> dict:
    """
    Executes the pytest test suite for the current workflow spec against
    the current dsl_candidate.

    If dsl_verification_passed is False, skips test execution (invalid
    candidates are not worth testing).

    STUB: Returns a hardcoded pass result for all tests.
    Real test execution is Session 04 (requires loading the test suite
    for the specific workflow_id from Dataset A).
    """
    if not state["dsl_verification_passed"]:
        return {"test_results": {}}

    # STUB: real implementation loads tests from dataset_a/{workflow_id}/
    # and runs them via subprocess against the dsl_candidate
    return {"test_results": {"stub_test": True}}


# --- Node 4: check_pass_or_repair --------------------------------------------

def check_pass_or_repair(state: WorkflowSynthState) -> str:
    """
    Decision node -- LangGraph conditional edge function.
    Returns a string key that LangGraph uses to route to the next node.

    Three routes:
        "pass"           -- verification passed and all tests pass
        "repair"         -- failed but attempts remain (< max_attempts)
        "record_failure" -- failed and all attempts exhausted
    """
    verification_passed = state["dsl_verification_passed"]
    tests_passed = all(state["test_results"].values()) if state["test_results"] else False
    attempt = state["repair_attempt"]
    max_attempts = state["max_attempts"]

    if verification_passed and tests_passed:
        return "pass"

    if attempt < max_attempts - 1:
        return "repair"

    return "record_failure"


# --- Node 5: repair_with_llm -------------------------------------------------

def repair_with_llm(state: WorkflowSynthState) -> dict:
    """
    Appends the current attempt to attempt_history, increments repair_attempt,
    and calls the LLM with a repair prompt that includes the specific errors.

    The repair prompt structure:
        - Original spec (immutable)
        - The failing YAML candidate
        - Type errors (if any)
        - Taint violations (if any)
        - Test failures (if any)
        - Attempt number / attempts remaining

    STUB: Appends history and increments counter; LLM call returns the same
    stub YAML. Real LLM integration is Session 04.
    """
    # Build the attempt record (append-only)
    attempt_record = {
        "attempt_number": state["repair_attempt"],
        "llm_sketch": state["llm_sketch"],
        "dsl_type_errors": state["dsl_type_errors"],
        "dsl_taint_violations": state["dsl_taint_violations"],
        "test_results": state["test_results"],
        "failure_category": _classify_attempt(state),
    }

    new_history = state["attempt_history"] + [attempt_record]

    # STUB: real implementation calls the LLM with the repair prompt
    stub_repaired_yaml = state["llm_sketch"]  # no real repair in stub

    return {
        "attempt_history": new_history,
        "repair_attempt": state["repair_attempt"] + 1,
        "llm_sketch": stub_repaired_yaml,
    }


# --- Node 6: translate_output ------------------------------------------------

def translate_output(state: WorkflowSynthState) -> dict:
    """
    Translates the verified dsl_candidate to n8n JSON and LangChain Python.

    STUB: Returns minimal placeholder outputs.
    Real adapters are Session 06 (n8n_adapter, langchain_adapter).
    """
    return {
        "final_n8n_json": {"stub": "n8n output", "workflow_id": state["dsl_candidate"].get("workflow_id")},
        "final_langchain_python": f"# LangChain stub for {state['dsl_candidate'].get('workflow_id')}",
    }


# --- Node 7: verify_output ---------------------------------------------------

def verify_output(state: WorkflowSynthState) -> dict:
    """
    Stage 2 verification: security checks on the translated n8n JSON
    and LangChain Python outputs.

    STUB: Returns passed with no errors.
    Real Stage 2 verification is Session 06.
    """
    return {
        "output_verification_passed": True,
        "output_errors": [],
        "synthesis_successful": True,
    }


# --- Node 8: record_failure --------------------------------------------------

def record_failure(state: WorkflowSynthState) -> dict:
    """
    Called when all attempts are exhausted.
    Classifies the failure from attempt_history and sets synthesis_successful = False.
    """
    category = classify_failure(state["attempt_history"])

    # Build a human-readable reason from the last attempt
    last_attempt = state["attempt_history"][-1] if state["attempt_history"] else {}
    reason_parts = []
    if last_attempt.get("dsl_type_errors"):
        reason_parts.append(f"type errors: {last_attempt['dsl_type_errors'][:1]}")
    if last_attempt.get("dsl_taint_violations"):
        reason_parts.append(f"taint violations: {last_attempt['dsl_taint_violations'][:1]}")
    if last_attempt.get("test_results"):
        failed = [k for k, v in last_attempt["test_results"].items() if not v]
        if failed:
            reason_parts.append(f"failed tests: {failed[:2]}")

    return {
        "synthesis_successful": False,
        "failure_reason": "; ".join(reason_parts) if reason_parts else "max attempts exceeded",
        "failure_category": category,
    }


# --- Helper functions --------------------------------------------------------

def _classify_attempt(state: WorkflowSynthState) -> str:
    """Classifies the failure category for a single attempt."""
    if state["dsl_type_errors"] and any("YAML" in e for e in state["dsl_type_errors"]):
        return "parse_error"
    if state["dsl_type_errors"]:
        return "type_error"
    if state["dsl_taint_violations"]:
        return "taint_violation"
    if state["test_results"] and not all(state["test_results"].values()):
        return "test_failure"
    return "max_attempts_exceeded"


def classify_failure(attempt_history: list[dict]) -> str:
    """
    Classifies the overall failure from the full attempt history.
    Uses the most frequent failure category across all attempts.
    This is the value stored in WorkflowSynthState.failure_category
    and used for the dissertation failure taxonomy.
    """
    if not attempt_history:
        return "max_attempts_exceeded"

    from collections import Counter
    categories = [a.get("failure_category", "max_attempts_exceeded") for a in attempt_history]
    return Counter(categories).most_common(1)[0][0]


def select_model(attempt: int) -> str:
    """
    Returns the LLM model ID for a given attempt number.
    Attempts 0-7: Claude Opus 4.7 (primary)
    Attempts 8-9: GPT-5.4 (fallback -- different model may find solutions Claude cannot)

    CONSTRAINT: Do not change the model selection logic without a journal entry.
    """
    if attempt <= 7:
        return "claude-opus-4-7"
    return "gpt-5.4"
