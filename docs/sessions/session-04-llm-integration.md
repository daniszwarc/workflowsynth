# WorkflowSynth -- Session 04: LLM Integration

**Date:** August 6, 2026
**DSR Phase:** Build (Week 28)
**Component:** Synthesis Engine -- LLM Integration
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Replace the stub LLM calls from Session 03 with real LangChain calls to
Claude Opus 4.7 and GPT-5.4. Write the system prompt and repair prompt
templates. Run the pipeline end-to-end with a real workflow spec for the
first time.

By the end of this session we have:

- `.env.example` -- key template committed to repo (no real values)
- `.env` -- real keys, gitignored, never committed
- `src/synthesis/prompts.py` -- system prompt + repair prompt template
- `src/synthesis/nodes.py` -- updated: stubs replaced with real LLM calls
- `src/synthesis/llm_client.py` -- LangChain client factory (Claude + GPT)
- `tests/unit/test_prompts.py` -- prompt construction tests (no API keys needed)
- `tests/integration/test_pipeline_e2e.py` -- first end-to-end test (requires keys)

---

## What Changes from Session 03

Session 03 built the graph structure with stubs. Session 04 makes two nodes real:

- `translate_to_dsl` -- calls the LLM to generate a YAML candidate from the spec
- `repair_with_llm` -- calls the LLM with a structured repair prompt

Everything else stays the same. `verify_dsl`, `run_tests`, `check_pass_or_repair`,
`record_failure` are already real. `translate_output` and `verify_output` remain
stubs until Session 06.

---

## Environment Setup

### `.env.example` (committed to repo)

```
# WorkflowSynth LLM Provider Keys
# Copy this file to .env and fill in your real keys.
# NEVER commit .env to the repository.

ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### `.env` (gitignored, never committed)

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### `.gitignore` addition

Add this line if not already present:

```
.env
```

---

## The Prompts

The prompts are the most critical part of this session. A bad prompt means
the LLM generates invalid DSL even on simple specs, wasting all 10 attempts.
A good prompt means the LLM gets it right on attempt 0 for most specs.

### System Prompt Design Principles

1. **Give the LLM the full vocabulary.** List all 25 ops explicitly. The LLM
   cannot invent ops it has been told are the complete list.

2. **Show the exact output format.** Include a concrete YAML example. LLMs
   are much better at format compliance when shown the exact structure.

3. **State the rules explicitly.** Type rules, auth rules, taint rules --
   all stated as hard constraints the LLM must follow, not suggestions.

4. **No prose, no explanation, only YAML.** The output must be parseable
   directly. Any prose wrapping the YAML will break the parser.

### System Prompt

```
You are WorkflowSynth, an AI system that generates enterprise workflow
specifications in a formal YAML DSL.

Your task: given a natural language workflow description, generate a
valid YAML workflow that uses ONLY the 25 approved DSL operations listed
below.

## Output format

Respond with ONLY valid YAML. No explanation, no prose, no markdown code
fences. The response must be parseable directly as YAML.

Required top-level fields:
  workflow_id: <snake_case identifier>
  steps: <list of steps>

Required per step:
  id: <unique snake_case identifier>
  op: <one of the 25 approved operations>

Optional per step:
  params: <dict of parameters>
  output: <variable name this step produces>

## The 25 approved operations

Data Operations:
  fetch_api         -- retrieve data from an external API endpoint
  filter_records    -- filter a dataset by condition
  transform_json    -- reshape or map JSON structure
  validate_schema   -- check data against a schema definition
  aggregate_data    -- group and summarise records
  merge_datasets    -- combine two datasets by key
  extract_field     -- pull a specific field from a record
  format_output     -- serialise data to a target format

Control Flow:
  route_to_step     -- conditional branching to a named step
  apply_rule        -- evaluate a business rule and return result
  loop_records      -- iterate over a collection
  parallel_execute  -- run two steps concurrently
  wait_for_condition -- pause until a condition is met
  handle_error      -- catch and route errors
  retry_step        -- retry a failed step N times
  terminate_workflow -- end execution with a status

Integration Operations:
  send_to_queue     -- publish a message to a queue
  log_audit         -- write an immutable audit log entry
  notify_user       -- send a notification to a user
  call_webhook      -- make an HTTP call to an external endpoint
  read_database     -- read records from a database table
  write_database    -- write records to a database table
  authenticate_user -- verify user identity and role
  encrypt_field     -- encrypt a sensitive data field
  call_subworkflow  -- invoke another workflow by ID

## Hard constraints

1. Use ONLY the 25 operations above. Any other op name is invalid.
2. Every step id must be unique within the workflow.
3. If a step references params.input, that variable must be declared
   as the output of a previous step.
4. Operations that require input (filter_records, transform_json,
   validate_schema, aggregate_data, merge_datasets, extract_field,
   format_output, write_database, send_to_queue, call_webhook,
   notify_user, encrypt_field) MUST declare params.input.
5. Any write_database or call_webhook step MUST be preceded by an
   authenticate_user step earlier in the workflow.
6. Data from fetch_api, read_database, call_webhook, or call_subworkflow
   is untrusted. It MUST pass through validate_schema, encrypt_field,
   transform_json, filter_records, or extract_field before reaching
   write_database, call_webhook, send_to_queue, notify_user, or log_audit.

## Example

workflow_id: invoice_approval_workflow
steps:
  - id: step_fetch_invoices
    op: fetch_api
    params:
      endpoint: "/api/invoices/pending"
    output: raw_invoices

  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices

  - id: step_authenticate
    op: authenticate_user
    params:
      role: "approver"
    output: auth_result

  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result
```

### Repair Prompt Template

The repair prompt is built dynamically from the current attempt's errors.
It always includes: the original spec, the failing YAML, the specific errors,
and the attempt count.

```python
def build_repair_prompt(
    original_spec: str,
    failing_yaml: str,
    type_errors: list[str],
    taint_violations: list[str],
    test_failures: dict,
    attempt_number: int,
    max_attempts: int,
) -> str:
    parts = [
        f"Attempt {attempt_number + 1} of {max_attempts} failed.",
        "",
        "## Original specification",
        original_spec,
        "",
        "## Your previous YAML (attempt {attempt_number})".format(
            attempt_number=attempt_number
        ),
        failing_yaml,
        "",
    ]

    if type_errors:
        parts += [
            "## Type errors to fix",
            *[f"- {e}" for e in type_errors],
            "",
        ]

    if taint_violations:
        parts += [
            "## Taint violations to fix",
            *[f"- {v}" for v in taint_violations],
            "",
        ]

    if test_failures:
        failed = [k for k, v in test_failures.items() if not v]
        if failed:
            parts += [
                "## Failed tests",
                *[f"- {t}" for t in failed],
                "",
            ]

    parts += [
        "Generate a corrected YAML workflow that fixes ALL of the above errors.",
        "Respond with ONLY valid YAML. No prose, no markdown fences.",
    ]

    return "\n".join(parts)
```

---

## File 1: `.env.example`

```
# WorkflowSynth LLM Provider Keys
# Copy this file to .env and fill in your real keys.
# NEVER commit .env to the repository.

ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## File 2: `src/synthesis/llm_client.py`

```python
# src/synthesis/llm_client.py
#
# LangChain LLM client factory for WorkflowSynth.
# Returns the appropriate LangChain chat model for a given attempt number.
#
# CONSTRAINT (Critical Constraint 6): Only Claude Opus 4.7 and GPT-5.4
# are approved providers. Do not introduce local models or other providers.
#
# Usage:
#   from workflowsynth.synthesis.llm_client import get_llm
#   llm = get_llm(attempt=0)
#   response = llm.invoke([HumanMessage(content="...")])

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(attempt: int):
    """
    Returns the LangChain chat model for the given attempt number.

    Attempts 0-7: Claude Opus 4.7 (primary)
    Attempts 8-9: GPT-5.4 (fallback)

    The fallback strategy is deliberate: if Claude has failed 8 times,
    a different model architecture may find a solution Claude cannot.
    Both providers are accessed via LangChain -- swapping providers
    requires no changes to the node code.
    """
    if attempt <= 7:
        return _get_claude()
    return _get_gpt()


def _get_claude() -> ChatAnthropic:
    """Returns a Claude Opus 4.7 LangChain client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and add your key."
        )
    return ChatAnthropic(
        model="claude-opus-4-7",
        api_key=api_key,
        max_tokens=2048,
        temperature=0.2,   # low temperature for deterministic DSL generation
    )


def _get_gpt() -> ChatOpenAI:
    """Returns a GPT-5.4 LangChain client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your key."
        )
    return ChatOpenAI(
        model="gpt-5.4",
        api_key=api_key,
        max_tokens=2048,
        temperature=0.2,
    )
```

**Note on temperature:** We use 0.2, not 0.0. At temperature 0.0 the LLM
always generates the same output -- if it fails once, it fails identically
on every attempt. At 0.2, there is enough variation for the repair loop
to explore different candidates while remaining deterministic enough for
reproducible evaluation. This is a deliberate choice.

---

## File 3: `src/synthesis/prompts.py`

```python
# src/synthesis/prompts.py
#
# Prompt templates for WorkflowSynth LLM calls.
#
# Two prompts:
#   SYSTEM_PROMPT      -- the base system prompt for all LLM calls
#   build_repair_prompt -- builds a dynamic repair prompt from attempt errors
#
# The system prompt is the most critical component of the synthesis engine.
# Any change to it must be logged in the Implementation Journal and tested
# against a representative sample of Dataset A before committing.

SYSTEM_PROMPT = """You are WorkflowSynth, an AI system that generates enterprise workflow \
specifications in a formal YAML DSL.

Your task: given a natural language workflow description, generate a \
valid YAML workflow that uses ONLY the 25 approved DSL operations listed below.

## Output format

Respond with ONLY valid YAML. No explanation, no prose, no markdown code fences. \
The response must be parseable directly as YAML.

Required top-level fields:
  workflow_id: <snake_case identifier>
  steps: <list of steps>

Required per step:
  id: <unique snake_case identifier>
  op: <one of the 25 approved operations>

Optional per step:
  params: <dict of parameters>
  output: <variable name this step produces>

## The 25 approved operations

Data Operations:
  fetch_api         -- retrieve data from an external API endpoint
  filter_records    -- filter a dataset by condition
  transform_json    -- reshape or map JSON structure
  validate_schema   -- check data against a schema definition
  aggregate_data    -- group and summarise records
  merge_datasets    -- combine two datasets by key
  extract_field     -- pull a specific field from a record
  format_output     -- serialise data to a target format

Control Flow:
  route_to_step     -- conditional branching to a named step
  apply_rule        -- evaluate a business rule and return result
  loop_records      -- iterate over a collection
  parallel_execute  -- run two steps concurrently
  wait_for_condition -- pause until a condition is met
  handle_error      -- catch and route errors
  retry_step        -- retry a failed step N times
  terminate_workflow -- end execution with a status

Integration Operations:
  send_to_queue     -- publish a message to a queue
  log_audit         -- write an immutable audit log entry
  notify_user       -- send a notification to a user
  call_webhook      -- make an HTTP call to an external endpoint
  read_database     -- read records from a database table
  write_database    -- write records to a database table
  authenticate_user -- verify user identity and role
  encrypt_field     -- encrypt a sensitive data field
  call_subworkflow  -- invoke another workflow by ID

## Hard constraints

1. Use ONLY the 25 operations above. Any other op name is invalid.
2. Every step id must be unique within the workflow.
3. If a step references params.input, that variable must be declared \
as the output of a previous step.
4. Operations that require input (filter_records, transform_json, \
validate_schema, aggregate_data, merge_datasets, extract_field, \
format_output, write_database, send_to_queue, call_webhook, \
notify_user, encrypt_field) MUST declare params.input.
5. Any write_database or call_webhook step MUST be preceded by an \
authenticate_user step earlier in the workflow.
6. Data from fetch_api, read_database, call_webhook, or call_subworkflow \
is untrusted. It MUST pass through validate_schema, encrypt_field, \
transform_json, filter_records, or extract_field before reaching \
write_database, call_webhook, send_to_queue, notify_user, or log_audit.

## Example

workflow_id: invoice_approval_workflow
steps:
  - id: step_fetch_invoices
    op: fetch_api
    params:
      endpoint: "/api/invoices/pending"
    output: raw_invoices

  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices

  - id: step_authenticate
    op: authenticate_user
    params:
      role: "approver"
    output: auth_result

  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result"""


def build_repair_prompt(
    original_spec: str,
    failing_yaml: str,
    type_errors: list[str],
    taint_violations: list[str],
    test_failures: dict,
    attempt_number: int,
    max_attempts: int,
) -> str:
    """
    Builds a repair prompt from the current attempt's errors.

    The repair prompt gives the LLM:
    - The original spec (so it never loses sight of the goal)
    - The failing YAML (so it knows what it produced)
    - The specific errors (so it knows exactly what to fix)
    - The attempt count (so it knows how many tries remain)

    Error messages from type_check() and taint_analysis() are already
    written to be useful in a repair prompt -- they reference the specific
    step, describe the problem, and suggest the fix.
    """
    parts = [
        f"Attempt {attempt_number + 1} of {max_attempts} failed.",
        "Generate a corrected YAML workflow that fixes ALL errors listed below.",
        "",
        "## Original specification",
        original_spec,
        "",
        f"## Your previous YAML (attempt {attempt_number})",
        failing_yaml,
        "",
    ]

    if type_errors:
        parts += [
            "## Type / structure errors to fix",
            *[f"- {e}" for e in type_errors],
            "",
        ]

    if taint_violations:
        parts += [
            "## Security violations to fix",
            *[f"- {v}" for v in taint_violations],
            "",
        ]

    if test_failures:
        failed = [k for k, v in test_failures.items() if not v]
        if failed:
            parts += [
                "## Failed tests",
                *[f"- {t}" for t in failed],
                "",
            ]

    parts += [
        "Respond with ONLY valid YAML. No prose, no markdown fences.",
    ]

    return "\n".join(parts)
```

---

## File 4: `src/synthesis/nodes.py` (updated)

Only `translate_to_dsl` and `repair_with_llm` change. All other nodes are
identical to Session 03. Showing only the updated functions -- replace them
in the existing file.

```python
# --- Updated imports (add to top of nodes.py) --------------------------------

from langchain_core.messages import SystemMessage, HumanMessage
from .llm_client import get_llm
from .prompts import SYSTEM_PROMPT, build_repair_prompt


# --- Node 1: translate_to_dsl (REAL -- replaces stub) ------------------------

def translate_to_dsl(state: WorkflowSynthState) -> dict:
    """
    Calls the LLM to translate the natural language spec into a YAML DSL candidate.

    On the first attempt (repair_attempt == 0), sends only the spec.
    On subsequent attempts, this node is NOT called -- repair_with_llm
    handles re-generation with error context. translate_to_dsl is only
    ever called once per synthesis run (the initial generation).

    Uses select_model() to choose the LLM provider for this attempt.
    """
    llm = get_llm(state["repair_attempt"])

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["natural_language_spec"]),
    ]

    response = llm.invoke(messages)
    yaml_string = response.content.strip()

    return {"llm_sketch": yaml_string}


# --- Node 5: repair_with_llm (REAL -- replaces stub) -------------------------

def repair_with_llm(state: WorkflowSynthState) -> dict:
    """
    Appends the current attempt to attempt_history, increments repair_attempt,
    and calls the LLM with a structured repair prompt.

    The repair prompt includes the original spec, the failing YAML, and all
    specific errors from type_check() and taint_analysis(). Error messages
    are already written to be useful in a repair prompt.

    CONSTRAINT: attempt_history is append-only. Never overwrite.
    CONSTRAINT: natural_language_spec is immutable. Always use the original.
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
    new_attempt = state["repair_attempt"] + 1

    # Build repair prompt from current errors
    repair_prompt = build_repair_prompt(
        original_spec=state["natural_language_spec"],
        failing_yaml=state["llm_sketch"],
        type_errors=state["dsl_type_errors"],
        taint_violations=state["dsl_taint_violations"],
        test_failures=state["test_results"],
        attempt_number=state["repair_attempt"],
        max_attempts=state["max_attempts"],
    )

    # Call the LLM (provider selected by attempt number)
    llm = get_llm(new_attempt)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=repair_prompt),
    ]

    response = llm.invoke(messages)
    repaired_yaml = response.content.strip()

    return {
        "attempt_history": new_history,
        "repair_attempt": new_attempt,
        "llm_sketch": repaired_yaml,
    }
```

---

## File 5: `tests/unit/test_prompts.py`

These tests verify prompt construction without requiring API keys.

```python
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
```

---

## File 6: `tests/integration/test_pipeline_e2e.py`

This is the first real end-to-end test. It requires API keys in `.env`.
It is in `tests/integration/` -- NOT `tests/unit/` -- so it is excluded
from the standard `pytest tests/unit/ -v` run.

```python
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
```

---

## File structure to create in the repo

```
workflowsynth/
  .env.example                          (new -- committed)
  src/
    synthesis/
      llm_client.py                     (new)
      prompts.py                        (new)
      nodes.py                          (updated -- replace translate_to_dsl
                                         and repair_with_llm only)
  tests/
    unit/
      test_prompts.py                   (new)
    integration/
      __init__.py                       (new -- empty)
      test_pipeline_e2e.py              (new)
```

---

## Dependencies

Add to requirements:

```
python-dotenv>=1.0
langchain-anthropic>=0.3
langchain-openai>=0.2
```

Install:

```bash
pip install python-dotenv langchain-anthropic langchain-openai
```

---

## How to run the tests

Unit tests (no API keys needed):

```bash
pytest tests/unit/ -v
```

Integration tests (requires .env with real keys):

```bash
pytest tests/integration/ -v
```

All unit tests from Sessions 01-03 plus the new prompt tests must pass.
The integration tests are run separately and are excluded from the CI suite.

---

## Implementation Journal

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- LLM Integration
Type: Decision
Description: Temperature set to 0.2 for all LLM calls, not 0.0.
Justification: At temperature 0.0, the LLM produces identical output on
  every attempt. If attempt 0 fails, attempts 1-9 fail identically --
  the repair loop adds no value. At 0.2, there is enough variation for
  the loop to explore different candidates while remaining deterministic
  enough for reproducible evaluation runs.
Dissertation Impact: Implementation section -- synthesis engine parameters.
  Note this in the reproducibility discussion.
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- Prompts
Type: Decision
Description: System prompt includes all 25 ops, 6 hard constraints, and
  a concrete YAML example. No markdown code fences in the example.
Justification: LLMs mirror the format of examples they are shown. If the
  example uses fences, the LLM output uses fences, breaking the parser.
  Raw YAML in the example produces raw YAML in the output.
Dissertation Impact: Implementation section -- prompt design. Relevant to
  the failure taxonomy (parse_error category).
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Synthesis Engine -- LLM Integration
Type: Decision
Description: translate_to_dsl is only called once per synthesis run
  (initial generation). repair_with_llm handles all subsequent attempts.
Justification: The natural language spec is immutable (Critical Constraint 5).
  translate_to_dsl has no error context -- it cannot use feedback.
  repair_with_llm has full error context and builds a targeted repair prompt.
  Routing repairs through repair_with_llm (not translate_to_dsl) ensures
  error context is always present from attempt 1 onward.
Dissertation Impact: Architectural Decision 2 -- LLM-Guided Iterative
  Refinement. Implementation section.
```

---

## Next Session

Session 05 -- Evidence Report (`src/verification/evidence_report.py`).

The evidence report is what makes WorkflowSynth compliance-aware (Architectural
Decision 5). Every verified workflow output must carry an explicit statement of
what was verified, what was not checked, and what remains the deploying
engineer's responsibility. This is the open-samd Pattern 1 requirement.
