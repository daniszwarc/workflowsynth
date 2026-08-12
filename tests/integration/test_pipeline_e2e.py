# tests/integration/test_pipeline_e2e.py
#
# End-to-end integration test for the WorkflowSynth pipeline.
# REQUIRES: ANTHROPIC_API_KEY and OPENAI_API_KEY in .env
#
# Run with: pytest tests/integration/ -v
# Do NOT include in the standard unit test run (pytest tests/unit/).

import pytest
import os
from dotenv import load_dotenv

load_dotenv()

# Skip all tests in this file if API keys are not available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set -- skipping integration tests"
)

from workflowsynth.synthesis.pipeline import build_pipeline, run_synthesis


# --- Test spec: simple invoice approval workflow ----------------------------
# This is the simplest possible real-world workflow.
# It should succeed on attempt 0 with a correct prompt.

SIMPLE_SPEC = """
Workflow: Invoice Approval

When a batch of invoices arrives from the external billing API, validate
each invoice against the invoice schema, authenticate the approver, and
store the validated invoices in the database.
"""


def test_simple_workflow_synthesis_succeeds():
    """
    The simplest real workflow should synthesise successfully within 10 attempts.
    This is the smoke test for the full pipeline.
    """
    pipeline = build_pipeline()
    state = run_synthesis(pipeline, SIMPLE_SPEC)

    assert state["synthesis_successful"] is True, (
        f"Synthesis failed after {state['repair_attempt']} attempts. "
        f"Last type errors: {state['dsl_type_errors']}. "
        f"Last taint violations: {state['dsl_taint_violations']}."
    )


def test_synthesis_produces_dsl_candidate():
    """Successful synthesis must produce a non-empty dsl_candidate."""
    pipeline = build_pipeline()
    state = run_synthesis(pipeline, SIMPLE_SPEC)

    if state["synthesis_successful"]:
        assert state["dsl_candidate"] != {}
        assert "workflow_id" in state["dsl_candidate"]
        assert "steps" in state["dsl_candidate"]
        assert len(state["dsl_candidate"]["steps"]) > 0


def test_attempt_history_is_populated():
    """
    attempt_history must be populated on failure attempts.
    On success on first attempt, history should be empty (no failures).
    """
    pipeline = build_pipeline()
    state = run_synthesis(pipeline, SIMPLE_SPEC)

    # If it succeeded on attempt 0, history is empty (correct)
    # If it needed repairs, history has records
    if state["repair_attempt"] == 0:
        assert state["attempt_history"] == []
    else:
        assert len(state["attempt_history"]) == state["repair_attempt"]


# --- Test spec: security-constrained workflow --------------------------------
# This spec deliberately describes a pattern that requires sanitisation.
# The LLM must include validate_schema before write_database.

SECURITY_SPEC = """
Workflow: Patient Data Ingestion

Read patient records from the external health API, validate the records
against the patient schema, authenticate the data engineer, and store
the validated records in the patient database.
"""


def test_security_constrained_workflow_passes_taint_check():
    """
    A workflow with external data sources must pass taint analysis.
    The LLM must include a sanitiser between the source and sink.
    """
    pipeline = build_pipeline()
    state = run_synthesis(pipeline, SECURITY_SPEC)

    # Whether it succeeds or not, the final state must not have
    # taint violations if synthesis_successful is True
    if state["synthesis_successful"]:
        assert state["dsl_taint_violations"] == []
