# WorkflowSynth — Session 03: LangGraph Pipeline

**Date:** August 6, 2026
**DSR Phase:** Build (Week 28)
**Component:** Synthesis Engine — LangGraph Pipeline
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Wire the DSL Layer (Session 01) and Verification Module (Session 02) into a
LangGraph stateful pipeline. This is the session where WorkflowSynth becomes
a real synthesis system — not just a verifier, but a loop that generates,
verifies, repairs, and retries.

By the end of this session we have:

- `src/synthesis/__init__.py` — public interface
- `src/synthesis/state.py` — `WorkflowSynthState` TypedDict (the full pipeline state)
- `src/synthesis/nodes.py` — all 8 LangGraph nodes
- `src/synthesis/pipeline.py` — graph definition, edges, conditional routing, compile
- `tests/unit/test_pipeline.py` — unit tests for nodes and routing logic

---

## What the Synthesis Engine Does

Sessions 01 and 02 built the verification machinery. But verification alone is
not synthesis -- it only tells you whether a candidate is correct. The synthesis
engine is what generates the candidates, feeds them to the verifier, interprets
the results, and decides what to do next: accept, repair, or give up.

The engine is implemented as a LangGraph stateful graph. LangGraph was chosen
(Architectural Decision 2) because it provides stateful conditional branching --
exactly what a verify-then-repair loop requires. Each iteration of the loop is
a pass through the graph nodes, and the state carries all context across passes.

The loop runs a maximum of 10 attempts. This is the pass@10 definition --
the primary evaluation metric. Do not change this number.

---

## The State Object

Every node in the graph reads from and writes to a single `WorkflowSynthState`
object. This is the complete pipeline state -- nothing lives outside it.

Understanding the state is the key to understanding the pipeline. Here is what
each field is for:

```
natural_language_spec   The original user input. IMMUTABLE -- never modified
                        after initialisation. The LLM always receives the
                        original spec, not a modified version.

llm_sketch              The raw YAML string produced by the LLM in the current
                        attempt. Overwritten on each attempt (only the current
                        sketch matters for verification).

dsl_candidate           The parsed WorkflowAST (as dict) from the current
                        attempt. None if parsing failed.

dsl_verification_passed True if type_check AND taint_analysis both returned
                        no errors. Set by verify_dsl node.

dsl_type_errors         List of error strings from type_check(). Empty if none.

dsl_taint_violations    List of error strings from taint_analysis(). Empty if none.

output_verification_passed  True if Stage 2 checks passed. Set by verify_output.

output_errors           List of Stage 2 error strings. Empty if none.

repair_attempt          Counter: 0 on first attempt, increments after each
                        failed attempt. Terminates at max_attempts (10).

max_attempts            Always 10. Never change this.

attempt_history         APPEND-ONLY list of dicts. Each failed attempt appends
                        one record. Never overwrite. The failure taxonomy and
                        ablation studies depend on this field being complete.

test_results            Dict of test_id -> pass/fail for the current attempt.

final_n8n_json          The verified n8n workflow JSON. None until success.

final_langchain_python  The verified LangChain Python code. None until success.

synthesis_successful    True if the pipeline ended with a verified output.

failure_reason          Human-readable reason for failure (last attempt).

failure_category        Taxonomy category from classify_failure(). One of:
                        "parse_error", "type_error", "taint_violation",
                        "test_failure", "output_error", "max_attempts_exceeded"
```

---

## The 8 LangGraph Nodes

```
[START]
   ↓
[translate_to_dsl]      LLM: NL spec → YAML DSL candidate
   ↓
[verify_dsl]            Stage 1: type_check + taint_analysis
   ↓
[run_tests]             Execute pytest test suite against the candidate
   ↓
[check_pass_or_repair]  Decision node -- routes to one of three paths
   ↓ PASS               ↓ FAIL, attempts < 10     ↓ FAIL, attempts == 10
[translate_output]      [repair_with_llm]          [record_failure]
   ↓                         ↓                          ↓
[verify_output]          → back to verify_dsl       [END -- failure]
   ↓
[END -- success + evidence report]
```

### Node responsibilities

**translate_to_dsl** -- calls the LLM with the natural language spec and the
attempt history. Returns the YAML string as `llm_sketch`. On the first attempt,
history is empty. On subsequent attempts, history contains all previous error
records -- this is how the LLM knows what to fix.

**verify_dsl** -- runs `parse_workflow()`, `type_check()`, and `taint_analysis()`
on `llm_sketch`. Populates `dsl_verification_passed`, `dsl_type_errors`, and
`dsl_taint_violations`. Even if parsing fails, the node does not raise -- it
records the errors in state and lets `check_pass_or_repair` decide.

**run_tests** -- executes the pytest test suite for this workflow spec against
the current `dsl_candidate`. Populates `test_results`. If `dsl_verification_passed`
is False, this node is skipped (no point running tests on an invalid candidate).

**check_pass_or_repair** -- the decision node. Three branches:
- PASS: `dsl_verification_passed` is True AND all tests pass → `translate_output`
- FAIL + attempts < 10: append to `attempt_history`, increment `repair_attempt`,
  build repair prompt → `repair_with_llm`
- FAIL + attempts == 10: → `record_failure`

**repair_with_llm** -- calls the LLM with the repair prompt (errors from current
attempt). The repair prompt includes: the original spec, the failing YAML, the
specific errors (type, taint, test), and the attempt number. Returns new
`llm_sketch`. Routes back to `verify_dsl` (not `translate_to_dsl` -- the spec
does not change, only the candidate).

**translate_output** -- translates the verified `dsl_candidate` (WorkflowAST)
to n8n JSON and LangChain Python. These are stub implementations in Session 03
-- the real adapters are built in Session 06.

**verify_output** -- Stage 2 checks on the translated outputs. Stub in Session 03.
Populates `output_verification_passed` and `output_errors`.

**record_failure** -- called when all 10 attempts are exhausted. Sets
`synthesis_successful = False`, classifies the failure from `attempt_history`,
and populates `failure_reason` and `failure_category`.

### Model selection

```python
def select_model(attempt: int) -> str:
    if attempt <= 7:
        return "claude-opus-4-7"   # primary: attempts 0-7
    return "gpt-5.4"               # fallback: attempts 8-9
```

The fallback to GPT-5.4 on the last two attempts is a deliberate strategy --
if Claude has failed 8 times, a different model may find a solution that Claude
cannot. This is also why LangChain is used for LLM calls: swapping providers
requires no code changes.

---

## File 1: `src/synthesis/__init__.py`

```python
# src/synthesis/__init__.py
# Public interface of the Synthesis Engine.

from .pipeline import build_pipeline, run_synthesis
from .state import WorkflowSynthState

__all__ = [
    "build_pipeline",
    "run_synthesis",
    "WorkflowSynthState",
]
```

---

## File 2: `src/synthesis/state.py`

```python
# src/synthesis/state.py
#
# WorkflowSynthState: the single state object carried through the LangGraph pipeline.
# Every node reads from and writes to this object.
#
# CONSTRAINT: natural_language_spec is immutable after initialisation.
# CONSTRAINT: attempt_history is append-only. Never overwrite existing records.
# CONSTRAINT: max_attempts is always 10. Never change this value.

from typing import TypedDict, Optional


class WorkflowSynthState(TypedDict):

    # Input -- immutable after initialisation
    natural_language_spec: str

    # Synthesis -- current attempt
    llm_sketch: str                     # raw YAML string from LLM
    dsl_candidate: dict                 # parsed AST as dict (None if parse failed)

    # Verification -- Stage 1 (DSL level)
    dsl_verification_passed: bool
    dsl_type_errors: list[str]
    dsl_taint_violations: list[str]

    # Verification -- Stage 2 (output level)
    output_verification_passed: bool
    output_errors: list[str]

    # Loop control
    repair_attempt: int                 # 0 on first attempt; increments on each failure
    max_attempts: int                   # Always 10 -- the pass@10 definition

    # Per-attempt history -- append-only, never overwritten
    # Each record: attempt_number, llm_sketch, type_errors, taint_violations,
    #              test_results, failure_category
    attempt_history: list[dict]

    # Test execution results
    test_results: dict                  # test_id -> True (pass) / False (fail)

    # Final outputs (None until synthesis succeeds)
    final_n8n_json: Optional[dict]
    final_langchain_python: Optional[str]
    synthesis_successful: bool

    # Failure taxonomy (populated by record_failure node)
    failure_reason: Optional[str]
    failure_category: Optional[str]


def initial_state(natural_language_spec: str) -> WorkflowSynthState:
    """
    Creates a fresh WorkflowSynthState for a new synthesis run.
    This is the only place where natural_language_spec is set.
    """
    return WorkflowSynthState(
        natural_language_spec=natural_language_spec,
        llm_sketch="",
        dsl_candidate={},
        dsl_verification_passed=False,
        dsl_type_errors=[],
        dsl_taint_violations=[],
        output_verification_passed=False,
        output_errors=[],
        repair_attempt=0,
        max_attempts=10,
        attempt_history=[],
        test_results={},
        final_n8n_json=None,
        final_langchain_python=None,
        synthesis_successful=False,
        failure_reason=None,
        failure_category=None,
    )
```

---

## File 3: `src/synthesis/nodes.py`

```python
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
```

---

## File 4: `src/synthesis/pipeline.py`

```python
# src/synthesis/pipeline.py
#
# LangGraph graph definition for the WorkflowSynth synthesis pipeline.
# Defines nodes, edges, conditional routing, and compiles the graph.
#
# Usage:
#   from workflowsynth.synthesis.pipeline import build_pipeline, run_synthesis
#   pipeline = build_pipeline()
#   final_state = run_synthesis(pipeline, "When an invoice arrives, validate and store it.")

from langgraph.graph import StateGraph, END
from .state import WorkflowSynthState, initial_state
from .nodes import (
    translate_to_dsl,
    verify_dsl,
    run_tests,
    check_pass_or_repair,
    repair_with_llm,
    translate_output,
    verify_output,
    record_failure,
)


def build_pipeline():
    """
    Builds and compiles the LangGraph synthesis pipeline.

    Graph structure:
        START -> translate_to_dsl -> verify_dsl -> run_tests
             -> check_pass_or_repair (conditional)
                  "pass"           -> translate_output -> verify_output -> END
                  "repair"         -> repair_with_llm -> verify_dsl (loop)
                  "record_failure" -> record_failure -> END

    Returns a compiled LangGraph runnable.
    """
    graph = StateGraph(WorkflowSynthState)

    # Register nodes
    graph.add_node("translate_to_dsl", translate_to_dsl)
    graph.add_node("verify_dsl", verify_dsl)
    graph.add_node("run_tests", run_tests)
    graph.add_node("translate_output", translate_output)
    graph.add_node("verify_output", verify_output)
    graph.add_node("repair_with_llm", repair_with_llm)
    graph.add_node("record_failure", record_failure)

    # Entry point
    graph.set_entry_point("translate_to_dsl")

    # Linear edges
    graph.add_edge("translate_to_dsl", "verify_dsl")
    graph.add_edge("verify_dsl", "run_tests")
    graph.add_edge("translate_output", "verify_output")
    graph.add_edge("verify_output", END)
    graph.add_edge("record_failure", END)

    # Repair loop: repair_with_llm goes back to verify_dsl (not translate_to_dsl)
    # The spec does not change -- only the candidate changes on repair.
    graph.add_edge("repair_with_llm", "verify_dsl")

    # Conditional routing from run_tests via check_pass_or_repair
    graph.add_conditional_edges(
        "run_tests",
        check_pass_or_repair,
        {
            "pass": "translate_output",
            "repair": "repair_with_llm",
            "record_failure": "record_failure",
        }
    )

    return graph.compile()


def run_synthesis(pipeline, natural_language_spec: str) -> WorkflowSynthState:
    """
    Runs the full synthesis pipeline for a natural language spec.

    Args:
        pipeline: compiled LangGraph pipeline from build_pipeline()
        natural_language_spec: the workflow description in plain English

    Returns:
        The final WorkflowSynthState after the pipeline completes.
        Check state["synthesis_successful"] to determine outcome.
    """
    state = initial_state(natural_language_spec)
    return pipeline.invoke(state)
```

---

## File 5: `tests/unit/test_pipeline.py`

```python
# tests/unit/test_pipeline.py
#
# Unit tests for the LangGraph pipeline nodes and routing logic.
#
# NOTE: These tests do NOT invoke the full compiled pipeline (that requires
# LLM API keys). Instead, they test each node in isolation and test the
# routing logic of check_pass_or_repair directly.
# Integration tests with the full pipeline are in tests/integration/.

import pytest
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

def test_repair_appends_to_history():
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

def test_repair_history_is_append_only():
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
        assert select_model(i) == "claude-opus-4-7"

def test_select_model_gpt_for_late_attempts():
    assert select_model(8) == "gpt-5.4"
    assert select_model(9) == "gpt-5.4"
```

---

## File structure to create in the repo

```
workflowsynth/
  src/
    synthesis/
      __init__.py
      state.py
      nodes.py
      pipeline.py
  tests/
    unit/
      test_pipeline.py
```

---

## Dependencies

Add to `requirements.txt`:

```
langgraph>=0.2
langchain>=0.3
langchain-anthropic>=0.3
langchain-openai>=0.2
```

Install:

```bash
pip install langgraph langchain langchain-anthropic langchain-openai
```

---

## How to run the tests

```bash
# from the repo root
pytest tests/unit/ -v
```

All 32 tests from Sessions 01 and 02 plus the new pipeline tests must pass.
The pipeline tests do NOT require LLM API keys -- they test nodes in isolation.

---

## What is a stub and why

Several nodes in Session 03 are stubs:

- `translate_to_dsl` -- returns hardcoded YAML instead of calling the LLM
- `repair_with_llm` -- increments the counter and appends history, but the
  "repaired" YAML is unchanged
- `translate_output` -- returns placeholder n8n and LangChain strings
- `verify_output` -- always returns passed

This is intentional. Session 03's goal is to wire the graph structure correctly
and verify that routing, state management, and the verify_dsl + run_tests nodes
(which are real, not stubs) work as expected. The LLM calls are the most complex
and expensive part -- they are introduced in Session 04 once the graph structure
is proven correct.

This mirrors the Karpathy principle: get the simplest version working end-to-end
first, then replace stubs with real implementations one at a time.

---

## Implementation Journal

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- LangGraph Pipeline
Type: Decision
Description: repair_with_llm routes back to verify_dsl, not translate_to_dsl.
Justification: The natural language spec is immutable (Critical Constraint 5).
  On repair, only the YAML candidate changes -- not the spec. Routing back to
  verify_dsl bypasses the LLM generation step and goes straight to verification,
  which is correct: repair_with_llm already produced the new llm_sketch.
Dissertation Impact: Architectural Decision 2 (LLM-Guided Iterative Refinement).
  Implementation section.
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- LangGraph Pipeline
Type: Decision
Description: Session 03 uses stub implementations for translate_to_dsl,
  repair_with_llm (LLM call), translate_output, and verify_output.
Justification: Karpathy principle -- wire the graph structure correctly first,
  then replace stubs with real implementations one at a time. This allows
  testing routing and state management without LLM API keys.
Dissertation Impact: Implementation section. Note this phased approach in the
  build narrative.
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- State
Type: Decision
Description: dsl_candidate stored as plain dict in state, not as WorkflowAST.
Justification: LangGraph state must be JSON-serialisable. WorkflowAST is a
  dataclass and not directly serialisable. The dict representation preserves
  all necessary information and can be reconstructed into a WorkflowAST if
  needed by downstream nodes.
Dissertation Impact: Implementation detail. Note in Implementation section.
```

---

## Next Session

Session 04 -- LLM Integration (`src/synthesis/prompts.py`).

Replace the stub LLM calls in `translate_to_dsl` and `repair_with_llm` with
real LangChain calls to Claude Opus 4.7 (and GPT-5.4 for fallback). Write the
system prompt and repair prompt templates. Test the full pipeline end-to-end
with a real workflow spec for the first time.
