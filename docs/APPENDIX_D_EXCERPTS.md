# Appendix D: Code and Artefact Excerpts

This appendix collects the code excerpts and artefacts referenced in the main
text, together with the exact commands used to install, test, and run the
system. All excerpts are quoted verbatim from the repository at the commit
hash given in Section D.6.

---

## D.1 The `VALID_OPS` Vocabulary

**File:** `src/dsl/constants.py` (full file, 119 lines — under the 150-line
threshold for full-text inclusion)

This is the complete, fixed 25-primitive vocabulary. No component in the
system may generate, accept, or route on an operation outside this set.

```python
"""Official WorkflowSynth DSL vocabulary.

These 25 operators are the only permitted vocabulary. No component may
accept an op that is not listed here.

CONSTRAINT: changing this vocabulary requires updating type_checker.py,
taint.py, and all Dataset A test suites. Log it in the Implementation Journal.
"""

# --- The 25 valid operators ---------------------------------------------------

VALID_OPS: set[str] = {
    # Data Operations (8)
    "fetch_api",
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",
    # Control Flow (8)
    "route_to_step",
    "apply_rule",
    "loop_records",
    "parallel_execute",
    "wait_for_condition",
    "handle_error",
    "retry_step",
    "terminate_workflow",
    # Integration Operations (9)
    "send_to_queue",
    "log_audit",
    "notify_user",
    "call_webhook",
    "read_database",
    "write_database",
    "authenticate_user",
    "encrypt_field",
    "call_subworkflow",
}

# --- Output type signatures ---------------------------------------------------
#
# Each operator declares an output type.
# The type checker uses this to validate that the output of one step
# is compatible with the input of the step that consumes it.
#
# Possible types:
#   "records"    -- list of records (list of dicts)
#   "record"     -- a single record (dict)
#   "boolean"    -- True / False
#   "string"     -- text
#   "any"        -- flexible output (type checking is permissive)
#   "none"       -- no output produced (side-effect only)
#   "auth_token" -- result of authenticate_user; required before write ops

OP_OUTPUT_TYPES: dict[str, str] = {
    # Data Operations
    "fetch_api": "records",
    "filter_records": "records",
    "transform_json": "records",
    "validate_schema": "records",
    "aggregate_data": "record",
    "merge_datasets": "records",
    "extract_field": "any",
    "format_output": "string",
    # Control Flow
    "route_to_step": "none",
    "apply_rule": "boolean",
    "loop_records": "none",
    "parallel_execute": "none",
    "wait_for_condition": "none",
    "handle_error": "none",
    "retry_step": "none",
    "terminate_workflow": "none",
    # Integration Operations
    "send_to_queue": "none",
    "log_audit": "none",
    "notify_user": "none",
    "call_webhook": "any",
    "read_database": "records",
    "write_database": "none",
    "authenticate_user": "auth_token",
    "encrypt_field": "string",
    "call_subworkflow": "any",
}

# --- Operators that require an input param ------------------------------------
#
# These operators must have params.input declared.
# The type checker verifies that the referenced input exists as the output
# of a previous step.

OPS_REQUIRING_INPUT: set[str] = {
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",
    "write_database",
    "send_to_queue",
    "call_webhook",
    "notify_user",
    "encrypt_field",
}

# --- Security rule: authenticate_user must precede these ops -----------------
#
# CONSTRAINT (Architectural Decision 3):
# Any step using these operators must have a preceding authenticate_user step.
# This rule is enforced in the type checker, not the taint analyser.

OPS_REQUIRING_AUTH: set[str] = {
    "write_database",
    "call_webhook",
}
```

---

## D.2 Taint Analysis Core

**File:** `src/verification/taint.py` (173 lines total — over the 150-line
threshold, so the two most representative excerpts are given below with exact
line ranges)

### D.2.1 The security model vocabulary (lines 26–50)

```python
# Ops whose output is always untrusted (external or unknown provenance)
TAINT_SOURCES: set[str] = {
    "fetch_api",
    "read_database",
    "call_webhook",
    "call_subworkflow",
}

# Ops where tainted input is a security violation
TAINT_SINKS: set[str] = {
    "write_database",
    "call_webhook",
    "send_to_queue",
    "notify_user",
    "log_audit",
}

# Ops that remove taint from their output
# (input was tainted, output is clean after this op)
TAINT_SANITISERS: set[str] = {
    "validate_schema",
    "encrypt_field",
    "transform_json",
    "filter_records",
    "extract_field",
}
```

### D.2.2 The entry point (lines 79–98)

```python
def taint_analysis(ast: WorkflowAST) -> list[TaintViolation]:
    """
    Runs taint analysis on a WorkflowAST.

    Returns a list of TaintViolation objects (empty = no violations = taint-safe).
    Each violation carries a message suitable for inclusion in a repair prompt.

    The analysis is a single forward pass through the ordered steps.
    Time complexity: O(n) where n is the number of steps.
    """
    violations: list[TaintViolation] = []

    # tainted_vars: maps variable_name -> step_id that introduced the taint
    # Using a dict (not a set) so we can report where the taint originated.
    tainted_vars: dict[str, str] = {}

    for step in ast.steps:
        _process_step(step, tainted_vars, violations)

    return violations
```

The per-step sink/source/sanitiser logic that `_process_step` implements
(lines 104–173) performs a single forward pass: a step whose op is in
`TAINT_SINKS` and whose input variable is currently tainted raises a
`TaintViolation` naming the sink, the tainted variable, and the originating
source step, with a message written to double as repair-prompt guidance.

---

## D.3 The LangGraph Pipeline Definition

**File:** `src/synthesis/pipeline.py` (full file, 92 lines — under the
150-line threshold for full-text inclusion)

```python
"""LangGraph graph definition for the WorkflowSynth synthesis pipeline.

Defines nodes, edges, conditional routing, and compiles the graph.

Usage:
    from workflowsynth.synthesis.pipeline import build_pipeline, run_synthesis
    pipeline = build_pipeline()
    final_state = run_synthesis(pipeline, "When an invoice arrives, validate and store it.")
"""

from langgraph.graph import END, StateGraph

from .nodes import (
    check_pass_or_repair,
    record_failure,
    repair_with_llm,
    run_tests,
    translate_output,
    translate_to_dsl,
    verify_dsl,
    verify_output,
)
from .state import WorkflowSynthState, initial_state


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
        },
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

This file registers exactly **seven** LangGraph nodes (`translate_to_dsl`,
`verify_dsl`, `run_tests`, `translate_output`, `verify_output`,
`repair_with_llm`, `record_failure`); `check_pass_or_repair` is the
conditional-edge decision function, not an eighth node.

---

## D.4 The Repair Prompt Template

**File:** `src/synthesis/prompts.py`, lines 138–177 (the 40-line body of
`build_repair_prompt`, full file is 177 lines — over the 150-line threshold)

```python
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

This is the body of `build_repair_prompt(original_spec, failing_yaml,
type_errors, taint_violations, test_failures, attempt_number, max_attempts)`.
It assembles the original spec, the LLM's own previous output, and the
specific structural, security, and test errors from that attempt into a
single message — the mechanism behind the repair loop's measured +25.83pp
contribution to pass@10.

---

## D.5 Example Task: `wf_btp_004` (Clinical Alert Generation)

### D.5.1 Specification

**File:** `datasets/dataset_a/wf_btp_004/spec.md`

```markdown
# Workflow: Clinical Alert Generation

## Context
The dashboard automatically generates clinical alerts based on deterministic threshold rules applied to the patient's lab values. No LLM involvement -- fixed clinical thresholds only.

## Trigger
The dashboard loads or a scheduled check runs.

## Steps
1. Read the most recent lab values from the clinical database.
2. Authenticate the requesting user.
3. Apply the neutrophil threshold rule: < 1.5 = warning, < 0.5 = critical.
4. Apply the hepatic panel rules: GOT and GPT thresholds.
5. Apply the CA 15-3 rise rule and RB1 detection rule.
6. Merge and format all alerts with severity levels.

## Constraints
- Alerts use deterministic threshold rules -- no LLM involved.
- Every alert links to the source document.
```

### D.5.2 Reference DSL

**File:** `datasets/dataset_a/wf_btp_004/reference_dsl.yaml`

```yaml
workflow_id: wf_btp_004
# domain: clinical_ai
# complexity: 3
# has_security_constraint: true
# primitive_count: 6
# source: Clinical AI Platform -- GET /alerts, deterministic rules on lab values
steps:
  - id: read_lab_values
    op: read_database
    params:
      table: lab_results
      filter: "date = most_recent"
    output: lab_values

  - id: authenticate_user
    op: authenticate_user
    params:
      role: "admin_or_patient"
    output: auth_result

  - id: apply_neutrophil_rule
    op: apply_rule
    params:
      input: lab_values
      rule: "neutrophil_threshold"
    output: neutrophil_alerts

  - id: apply_hepatic_rules
    op: apply_rule
    params:
      input: lab_values
      rule: "hepatic_panel_thresholds"
    output: hepatic_alerts

  - id: apply_tumor_marker_rules
    op: apply_rule
    params:
      input: lab_values
      rule: "tumor_marker_rules"
    output: tumor_alerts

  - id: merge_and_format_alerts
    op: merge_datasets
    params:
      input: neutrophil_alerts
      secondary: hepatic_alerts
      join_key: patient_id
    output: all_alerts
```

### D.5.3 Evidence Report Fragment

Generated by invoking the verification module (`type_check`, `taint_analysis`,
`generate_evidence_report`) directly against the reference DSL above — no
LLM call, no experiment script, no write to `results/`:

```json
{
  "workflow_id": "wf_btp_004",
  "generated_at": "2026-10-21T14:24:14.587698+00:00",
  "synthesis_attempts": 1,
  "verified": [
    "DSL vocabulary compliance: all 6 steps use valid operations from the 25-primitive vocabulary (apply_rule, authenticate_user, merge_datasets, read_database).",
    "Structural validity: all required fields present, 6 step IDs unique, all params correctly typed.",
    "Type safety: all params.input references resolve to previously declared output variables. All type compositions are valid.",
    "Taint safety: data from external sources (read_database) is sanitised before reaching critical sinks. No taint violations detected.",
    "Test suite: 1/1 tests pass against this DSL candidate."
  ],
  "not_checked": [
    "Business logic correctness: the verification module checks structural and security properties only. It does not verify that the workflow implements the correct business logic for the target domain.",
    "Integration-specific security: n8n and LangChain have their own security models. Stage 2 checks cover the translated output structure, not the runtime security of the target platform."
  ],
  "engineer_responsibilities": [
    "Review the workflow logic against the business requirements it is meant to implement. The system verifies structure and security -- not business correctness.",
    "Confirm that the authenticate_user role requirements match the actual permission model of the deployment environment."
  ],
  "raw_type_errors": [],
  "raw_taint_violations": []
}
```

This illustrates Architectural Decision 5 directly: the report is not a
binary pass/fail. It names exactly what was verified (vocabulary compliance,
structural validity, type safety, taint safety, test results), what falls
outside the verification module's scope (business logic correctness,
platform-specific runtime security), and what remains the deploying
engineer's responsibility — the mechanism that avoids the "disclaimer trap."

### D.5.4 Why `wf_btp_003` and `wf_mm_008` were not used here

`wf_btp_003` and `wf_mm_008` are the task ids cited elsewhere in the
dissertation, so they were checked first. Both were found unsuitable for this
appendix, for two different reasons established by direct investigation
(read-only; no API calls, no writes to `results/`):

**Why their reference DSLs fail the current taint rule.** Running
`taint_analysis()` on each `reference_dsl.yaml` directly finds:

- `wf_btp_003`: step `search_raw_documents` (`op: read_database`, a
  `TAINT_SOURCE`) taints `validated_context` via step
  `merge_and_validate_context` (`op: merge_datasets`). `merge_datasets` is
  **not** in `TAINT_SANITISERS` despite the step's id implying validation —
  it is a plain propagator, so the taint passes straight through to step
  `generate_response` (`op: call_webhook`, a `TAINT_SINK`), producing one
  violation.
- `wf_mm_008`: step `download_pdf` (`op: fetch_api`, a source) feeds directly
  into `extract_text` (`op: call_webhook`), which is simultaneously a
  `TAINT_SOURCE` and a `TAINT_SINK` in the current vocabulary — so an
  unsanitised call into it is flagged. Separately, `structure_via_ai`
  (`op: call_webhook`, a source) taints two downstream sinks,
  `write_markdown` (`op: write_database`) and `commit_and_push`
  (`op: log_audit`), neither of which passes through a sanitiser
  (`validate_schema`, `encrypt_field`, `transform_json`, `filter_records`,
  or `extract_field`) first.

In both cases the reference author's step names ("validate", "structure")
describe the intended business behaviour, but the actual `op` used
(`merge_datasets`, `call_webhook`) is not one the taint analyser treats as a
sanitiser. This is a property of the hand-written reference files, not of
the live system under test.

**Whether the evaluation uses the reference DSLs.** It does not. A
repository-wide search (`grep -rn "reference_dsl" src/ scripts/`) returns no
matches: `EvaluationRunner` and the baselines read only `index.yaml`,
`spec.md`, and the `tests/test_*.py` pytest suite for each task
(`src/evaluation/runner.py`, line ~662 and `_load_index`). `reference_dsl.yaml`
is documentation only — a human-authored "what a correct answer looks like"
artefact for readers of the dataset, consulted by no code path in
`pass_at_k`, `security_pass_at_10`, or any other reported metric. The two
violations above therefore have no bearing on the reported pass@10 or
security_pass@10 figures.

**Why the stored `wf_mm_008` result could not be substituted either.**
`results/session_09/full/wf_mm_008.json` (inspected read-only) shows
`"success": false` with `attempts_used: 10` — the task never passed under
the `full` condition. It also fails under `no_repair`, `no_verify`, and
`no_taint`; its last attempt's failure is a parse error (`Step at index 41
(id='route'): missing required field 'op'`), unrelated to taint at all.
There is no "winning attempt-3 DSL" for `wf_mm_008` anywhere in the stored
results to substitute in. `wf_btp_004` is kept for this appendix because,
among the tasks checked, it is the one whose reference DSL both parses and
passes the current taint and type rules cleanly, giving a self-consistent,
directly-quotable evidence report.

---

## D.6 Repository Tree, Commands, and Provenance

### D.6.1 Repository tree (two levels deep, tracked files only)

```
workflowsynth/
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements-lock.txt
├── datasets/
│   ├── dataset_a/            # 133 real enterprise workflow tasks
│   └── dataset_b/            # 60 public-benchmark-adapted tasks
├── docs/
│   └── sessions/             # Implementation session notes (01-09)
├── examples/
│   └── invoice_processing.md # Demo spec for scripts/synthesize.py
├── results/
│   └── session_09/           # Final experiment results (6 conditions)
├── scripts/
│   ├── analyze_results.py    # Statistical analysis -> analysis_summary.json
│   ├── run_evaluation.py     # Evaluation CLI (ablations + baselines)
│   ├── synthesize.py         # Single-spec synthesis CLI
│   └── verify_model_ids.py
├── src/
│   ├── dsl/                  # Parser, AST, type checker, VALID_OPS
│   ├── synthesis/             # LangGraph pipeline, nodes, prompts, state
│   ├── verification/          # Taint analysis, evidence report
│   ├── evaluation/            # Runner, baselines, metrics, ablation
│   └── integration/            # n8n and LangChain adapters
└── tests/
    ├── unit/                 # 137 tests, no API calls
    └── integration/           # 6 tests, require ANTHROPIC_API_KEY
```

### D.6.2 Exact commands

Install and test:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/unit/ -v
```

Run one synthesis (requires `ANTHROPIC_API_KEY`, spends API credits):

```bash
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
python scripts/synthesize.py examples/invoice_processing.md --out ./output
```

### D.6.3 Test count and commit hash

- **Total: 143 tests (137 unit, 6 integration requiring an API key).**
- Chapter 5 results were produced at commit
  `4452079af68ea87ec0c8ae9ac17a3f8afa6c0a73` (2026-09-07); later commits
  changed documentation and code style only (tests and analysis output
  verified unchanged).
- **Commit hash (HEAD at time of writing this appendix):**
  `87c65dd96fc1abc598f42f17f081fad2636b9529`
- **Suggested tag for the submission snapshot:** `v1.0-submission`
  (not yet created — pending confirmation).
