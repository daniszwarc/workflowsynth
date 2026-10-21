# Appendix D: Code and Artefact Excerpts

This appendix collects the code excerpts and artefacts referenced in the main
text, together with the exact commands used to install, test, and run the
system. All excerpts are quoted verbatim from the repository at
<https://github.com/daniszwarc/workflowsynth>, at the commit hash given in
Section D.6.

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
specific structural and security errors and the names of the failed tests
from that attempt into a single message — the mechanism behind the repair
loop's measured +25.83pp contribution to pass@10. Note that the "Failed
tests" section lists only failing test node ids (e.g.
`test_wf_x.py::test_foo`); no assertion message or traceback is captured
by the pytest hook upstream, so a test failure gives the LLM a weaker
signal than a structural or security error does.

---

## D.5 Example Task: `wf_ae_001` (PDF Article Extraction via AI Vision)

This example is taken from the official run, `results/session_09/full/wf_ae_001.json`
(`full` condition, `success: true`, `attempts_used: 2`) — not from
`reference_dsl.yaml`, which is never read by the evaluation code (see
Section D.2's taint discussion for the general point). Attempt 0 (the
candidate's first try) failed with a taint violation; attempt 1 (its
second try, after one repair) is the final accepted DSL.

### D.5.1 Specification

**File:** `datasets/dataset_a/wf_ae_001/spec.md` (full file, 19 lines)

```markdown
# Workflow: PDF Article Extraction via AI Vision

## Context
An economics magazine automates the extraction of article content from PDF files stored in Google Drive. Each PDF is sent to an AI vision model that extracts structured content including title, author, section, lead, body text, highlighted quotes, and sidebars.

## Trigger
A PDF file is found in the pending articles folder in Google Drive.

## Steps
1. Search Google Drive for PDF files in the pending articles folder.
2. Download the PDF file binary from Google Drive.
3. Send the PDF binary to the AI vision API with a structured extraction prompt.
4. Parse the AI response JSON, stripping any markdown fences.
5. Validate that required fields are present (title, section, content).

## Constraints
- The AI must handle two formats: single article and multiple book reviews (es_multiple = true).
- Double quotes inside content must be replaced with single quotes to preserve JSON validity.
- The lead field must never be empty.
```

### D.5.2 Attempt 0: the taint violation

**File:** `results/session_09/full/wf_ae_001.json`, the `dsl_taint_violations`
entry of `attempt_history[0]` (line 23 of the JSON file). Quoted verbatim:

> Step 'send_to_vision_api' (op: call_webhook): tainted variable 'raw_pdf_binary' reached a sink without sanitisation. Taint introduced at step 'download_pdf' via a source operation. Add a sanitising step (validate_schema, encrypt_field, transform_json, filter_records, or extract_field) between step 'download_pdf' and step 'send_to_vision_api'.

Attempt 0's candidate sent `download_pdf`'s output (`raw_pdf_binary`, from
`fetch_api`, a `TAINT_SOURCE`) straight into `send_to_vision_api`
(`call_webhook`, a `TAINT_SINK`) with no sanitising step in between.

### D.5.3 Attempt 1: the final accepted DSL

**File:** `results/session_09/full/wf_ae_001.json`, the `llm_sketch` field of
`attempt_history[1]` (line 33 of the JSON file; the field is one JSON string,
reproduced here as the 183-line YAML document it decodes to). This is the
candidate the pipeline actually accepted and ran the test suite against —
not a reference file:

```yaml
workflow_id: pdf_article_extraction_via_ai_vision
steps:
  - id: step_authenticate
    op: authenticate_user
    params:
      role: "system_service_account"
    output: auth_result

  - id: step_search_drive
    op: fetch_api
    params:
      endpoint: "/api/google-drive/search"
      query:
        folder: "pending_articles"
        mime_type: "application/pdf"
    output: raw_pdf_list

  - id: step_validate_pdf_list
    op: validate_schema
    params:
      input: raw_pdf_list
      schema: pdf_file_list_schema
    output: validated_pdf_list

  - id: step_loop_pdfs
    op: loop_records
    params:
      input: validated_pdf_list
      steps:
        - download_pdf
        - validate_pdf_binary
        - send_to_vision_api
        - parse_ai_response
        - sanitize_quotes
        - validate_extracted_fields
        - apply_lead_rule
        - apply_format_rule
        - route_by_format
        - write_single_article
        - write_multiple_reviews
        - log_extraction
    output: loop_result

  - id: download_pdf
    op: fetch_api
    params:
      endpoint: "/api/google-drive/download"
      file_id_from: validated_pdf_list
    output: raw_pdf_binary

  - id: validate_pdf_binary
    op: validate_schema
    params:
      input: raw_pdf_binary
      schema: pdf_binary_schema
    output: validated_pdf_binary

  - id: send_to_vision_api
    op: call_webhook
    params:
      input: validated_pdf_binary
      url: "https://ai-vision.example.com/extract"
      method: "POST"
      headers:
        Content-Type: "application/pdf"
      body_prompt: >
        Extract structured content from this PDF article. Return JSON with fields:
        title, author, section, lead, body, highlighted_quotes, sidebars.
        If the PDF contains multiple book reviews, set es_multiple to true and
        return an array of articles. Otherwise set es_multiple to false.
    output: raw_ai_response

  - id: parse_ai_response
    op: transform_json
    params:
      input: raw_ai_response
      mapping:
        operation: "strip_markdown_fences_and_parse"
    output: parsed_ai_json

  - id: sanitize_quotes
    op: transform_json
    params:
      input: parsed_ai_json
      mapping:
        operation: "replace_double_quotes_with_single_in_content_fields"
        fields:
          - "title"
          - "lead"
          - "body"
          - "highlighted_quotes"
          - "sidebars"
    output: sanitized_ai_json

  - id: validate_extracted_fields
    op: validate_schema
    params:
      input: sanitized_ai_json
      schema:
        required_fields:
          - "title"
          - "section"
          - "body"
          - "lead"
          - "es_multiple"
    output: validated_article_data

  - id: apply_lead_rule
    op: apply_rule
    params:
      rule: "lead_field_must_not_be_empty"
      condition: "validated_article_data.lead != '' AND validated_article_data.lead != null"
      on_fail: "terminate_with_error"
    output: lead_check_result

  - id: apply_format_rule
    op: apply_rule
    params:
      rule: "determine_article_format"
      condition: "validated_article_data.es_multiple == true"
    output: format_flag

  - id: route_by_format
    op: route_to_step
    params:
      condition: "format_flag == true"
      true_step: write_multiple_reviews
      false_step: write_single_article

  - id: write_single_article
    op: write_database
    params:
      input: validated_article_data
      table: "articles"
      mode: "insert"
    output: write_single_result

  - id: write_multiple_reviews
    op: write_database
    params:
      input: validated_article_data
      table: "book_reviews"
      mode: "insert_batch"
    output: write_reviews_result

  - id: log_extraction
    op: log_audit
    params:
      input: validated_article_data
      event: "pdf_article_extracted"
      details:
        source: "google_drive_pending_articles"
        es_multiple: "format_flag"
    output: audit_log_result

  - id: step_handle_error
    op: handle_error
    params:
      on_error: "notify_and_terminate"
      steps:
        - step_notify_error
        - step_terminate_on_error

  - id: step_notify_error
    op: notify_user
    params:
      input: validated_article_data
      recipient: "editorial_ops_team"
      channel: "email"
      message: "PDF article extraction failed. Please review the pending articles folder."
    output: error_notification_result

  - id: step_terminate_on_error
    op: terminate_workflow
    params:
      status: "failed"
      reason: "Extraction or validation error encountered"

  - id: step_terminate_success
    op: terminate_workflow
    params:
      status: "completed"
      reason: "All pending PDFs extracted and stored successfully"
```

The only change from attempt 0 is the insertion of `validate_pdf_binary`
(`op: validate_schema`) between `download_pdf` and `send_to_vision_api`, and
retargeting `send_to_vision_api`'s `input` from `raw_pdf_binary` to
`validated_pdf_binary` — exactly the sanitising step the attempt-0 violation
message asked for.

### D.5.4 Evidence Report Fragment

Generated by invoking the verification module (`type_check`, `taint_analysis`,
`generate_evidence_report` — `src/verification/evidence_report.py`) directly
against the attempt-1 DSL above, using the real stored `test_results` from
`attempt_history[1]`: no LLM call, no experiment script, no write to
`results/`.

```json
{
  "workflow_id": "pdf_article_extraction_via_ai_vision",
  "generated_at": "2026-10-21T19:30:48.722728+00:00",
  "synthesis_attempts": 2,
  "verified": [
    "DSL vocabulary compliance: all 20 steps use valid operations from the 25-primitive vocabulary (apply_rule, authenticate_user, call_webhook, fetch_api, handle_error, log_audit, loop_records, notify_user, route_to_step, terminate_workflow, transform_json, validate_schema, write_database).",
    "Structural validity: all required fields present, 20 step IDs unique, all params correctly typed.",
    "Type safety: all params.input references resolve to previously declared output variables. All type compositions are valid.",
    "Authentication precedence: every write_database and call_webhook step is preceded by an authenticate_user step.",
    "Taint safety: data from external sources (call_webhook, fetch_api) is sanitised before reaching critical sinks. No taint violations detected.",
    "Test suite: 4/4 tests pass against this DSL candidate."
  ],
  "not_checked": [
    "Business logic correctness: the verification module checks structural and security properties only. It does not verify that the workflow implements the correct business logic for the target domain.",
    "Rate limits and quotas: external API calls are not checked for rate limiting, authentication token expiry, or quota constraints.",
    "Schema correctness: validate_schema is verified as a sanitiser. The correctness of the schema definition itself is not verified.",
    "Integration-specific security: n8n and LangChain have their own security models. Stage 2 checks cover the translated output structure, not the runtime security of the target platform."
  ],
  "engineer_responsibilities": [
    "Review the workflow logic against the business requirements it is meant to implement. The system verifies structure and security -- not business correctness.",
    "Verify that the schemas used in validate_schema steps are current and correct for the target environment.",
    "Confirm that all external endpoints are authorised and that credentials are managed securely outside the workflow definition.",
    "Confirm that the authenticate_user role requirements match the actual permission model of the deployment environment.",
    "Review write_database steps for data integrity constraints, transaction requirements, and backup procedures in the target database environment."
  ],
  "raw_type_errors": [],
  "raw_taint_violations": []
}
```

This illustrates Architectural Decision 5 directly: the report is not a
binary pass/fail. It names exactly what was verified (vocabulary compliance,
structural validity, type safety, authentication precedence, taint safety,
test results), what falls outside the verification module's scope (business
logic correctness, schema correctness, platform-specific runtime security),
and what remains the deploying engineer's responsibility — the mechanism
that avoids the "disclaimer trap." It is also a direct, end-to-end
illustration of the repair loop (D.4) acting on a real taint violation
(D.5.2) and producing a verifiably clean accepted candidate (D.5.3) in the
official experimental run.

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
- **Commit hash:** the commit tagged v1.0-submission
- **Suggested tag for the submission snapshot:** `v1.0-submission`
