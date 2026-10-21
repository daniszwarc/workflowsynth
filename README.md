# WorkflowSynth

> **MSc AI Capstone -- Automated Generation of Correct and Secure Enterprise Workflows via LLM-Guided Programme Synthesis and Formal Verification**
> University of Liverpool . MSc Artificial Intelligence . Jan 2026 - Nov 2026

Repository: https://github.com/daniszwarc/workflowsynth

---

## Installation and Quick Start

**Requires Python >= 3.10.** On macOS the system `python3` is typically 3.9.x and will fail
the install below -- use a 3.10+ interpreter explicitly (e.g. `python3.11` via Homebrew).

```bash
# 1. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install the package with dev dependencies (pytest, ruff)
pip install -e ".[dev]"

# 2b. For an exact reproduction of the verified environment, use the lock
#     file instead (pins every dependency to the version this was tested on):
#     pip install -r requirements-lock.txt && pip install -e . --no-deps

# 3. Run the unit test suite (no API keys required, no network calls)
pytest tests/unit/ -v

# 4. Run one end-to-end synthesis example (REQUIRES ANTHROPIC_API_KEY, spends API credits)
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
python scripts/synthesize.py examples/invoice_processing.md --out ./output
```

Note: `tests/integration/` makes real LLM calls and is skipped automatically unless
`ANTHROPIC_API_KEY` is set. Do not run `pytest` (bare) with API keys configured unless you
intend to spend API credits -- always target `tests/unit/` for routine checks.

**Reproducing the evaluation** (full experiment run -- spends significant API credits, do not
run casually):

```bash
python scripts/run_evaluation.py \
  --condition full \
  --dataset datasets/dataset_a \
  --results results/my_run
```

Valid `--condition` values are the six experimental conditions: `full`, `no_repair`,
`no_verify`, `no_taint`, `baseline_pure_llm`, `baseline_langchain`. See
`python scripts/run_evaluation.py --help` for all options.

---

## Research Question

**Primary:**
> To what extent can combining LLM-guided programme synthesis with formal verification improve the automatic generation of correct and secure enterprise-grade workflows from natural language specifications, compared to unconstrained LLM generation?

**Secondary:**
> 1. **Correctness:** How effectively does sketch-guided synthesis constrain the LLM search space to reduce hallucination while preserving the expressiveness needed for real enterprise workflow patterns?
> 2. **Security:** Can lightweight formal verification -- specifically type safety checking and taint analysis -- detect and eliminate security vulnerabilities in synthesised enterprise workflows without requiring full theorem-proving infrastructure?
> 3. **Viability:** How does WorkflowSynth's hybrid neural-symbolic approach compare to existing state-of-the-art baselines in enterprise workflow automation?

---

## The Problem

Enterprise workflow development consumes 60-80% of IT budgets ($85B annually in the US). LLMs can generate workflows rapidly but cannot guarantee correctness or security in production -- 62% of LLM-generated programs contain formally verified vulnerabilities (Tihanyi et al., 2025). Prompt engineering alone achieves at most 77% vulnerability reduction (Aldosari & Aldawsari, 2026), which is insufficient for enterprise deployment. WorkflowSynth addresses this gap by combining LLM generation with formal verification in a single integrated pipeline.

---

## System Architecture

WorkflowSynth is a Python-based system with four components forming a sequential pipeline:

```
Natural Language Specification (SKILL.md format)
                    |
                    v
    +-------------------------------+
    |       SYNTHESIS ENGINE        |
    |   LangGraph + LangChain       |
    |                               |
    |  LLM translates spec -> DSL   |
    |  Iterative verify-then-repair |
    |  loop (max 10 attempts)       |
    +---------------+---------------+
                    |
                    v
    +-------------------------------+
    |          DSL LAYER            |
    |     Python + Lark parser      |
    |                               |
    |  Formal YAML-based internal   |
    |  representation               |
    |  25 constrained primitives    |
    |  Type system enforcement      |
    +---------------+---------------+
                    |
                    v
    +-------------------------------+
    |     VERIFICATION MODULE       |
    |       Custom Python           |
    |                               |
    |  Stage 1: DSL-level           |
    |  - Type safety checker        |
    |  - Taint analysis engine      |
    |                               |
    |  Stage 2: Output-level        |
    |  - Generates evidence report  |
    |  - Attaches it to the output  |
    +---------------+---------------+
                    |
                    v
    +-------------------------------+
    |      INTEGRATION LAYER        |
    |     Python serialisers        |
    |                               |
    |  n8n JSON adapter             |
    |  LangChain Python adapter     |
    +-------------------------------+
```

---

## LangGraph Pipeline

The synthesis engine uses a stateful LangGraph pipeline implementing the verify-then-repair loop:

```
[START]
   |
   v
[translate_to_dsl]     LLM translates NL spec to YAML DSL candidate
   |
   v
[verify_dsl]           Type safety + taint analysis on DSL
   |
   v
[run_tests]            Execute candidate against test suite
   |
   v
[check_pass_or_repair] Decision node
   |                        |                        |
   v (pass)                 v (fail, attempts < 10)  v (fail, attempts == 10)
[translate_output]     [repair_with_llm]         [record_failure]
   |                        |                        |
   v                        +------> [verify_dsl]    v
[verify_output]                                  [END -- failure]
   |
   v
[END -- success]
```

---

## Technology Stack

| Component | Technology | Reason |
|---|---|---|
| DSL Parser | Python + Lark | Formal grammar, deterministic parsing |
| LLM Orchestration | LangChain | Provider abstraction, prompt management |
| Pipeline Orchestration | LangGraph | Stateful synthesis loop, conditional branching |
| Verification Module | Custom Python | Deterministic formal methods |
| n8n Adapter | Python JSON serialiser | n8n is JSON-based |
| LangChain Adapter | LangChain | Natural fit |
| Primary LLMs | Claude Opus 4.6 (attempts 1-8) + GPT-5.4 (attempts 9-10) | Swappable via LangChain abstraction |
| Testing | pytest | Standard Python testing |

The attempt 9/10 switch to GPT-5.4 is unconditional on attempt number (`select_model`, `src/synthesis/nodes.py:380-390`; `get_llm`, `src/synthesis/llm_client.py:23-37`) -- it is not triggered by Claude errors, timeouts, or rate limits, and it is not a dormant fallback: in the stored `results/session_09/` data, 16 tasks in the `full` condition alone (30, 14, and 0 in `no_verify`, `no_taint`, and `no_repair` respectively) have an attempt with `attempt_number >= 8`, meaning GPT-5.4 actually produced those attempts, including at least one accepted success (`wf_ae_006`, `full`, attempt 9). `baseline_pure_llm` and `baseline_langchain` both call `get_llm(0)` and are single-attempt, so they use Claude Opus 4.6 only and never reach the GPT-5.4 branch.

---

## DSL -- 25 Primitives

The formal vocabulary WorkflowSynth generates. No operations outside this list may be synthesised.

**Data Operations (8):** `fetch_api` `filter_records` `transform_json` `validate_schema` `aggregate_data` `merge_datasets` `extract_field` `format_output`

**Control Flow (8):** `route_to_step` `apply_rule` `loop_records` `parallel_execute` `wait_for_condition` `handle_error` `retry_step` `terminate_workflow`

**Integration Operations (9):** `send_to_queue` `log_audit` `notify_user` `call_webhook` `read_database` `write_database` `authenticate_user` `encrypt_field` `call_subworkflow`

---

## Key Architectural Decisions

| Decision | Choice | Justification |
|---|---|---|
| DSL Input Format | Two-layer: SKILL.md NL input -> formal YAML DSL internally | Separates human-friendly interface from formally verifiable representation. Based on Murphy et al. (2024). |
| Synthesis Search | LLM-guided iterative refinement, max 10 attempts | Verify-then-repair pattern (Tihanyi et al., 2025). Bottom-up enumeration rejected as impractical. |
| Verification Scope | Two-stage: DSL-level + output-level | DSL-only rejected -- cannot detect vulnerabilities introduced during translation. |
| Pipeline State | Full state object, append-only attempt history | Minimal state rejected -- per-attempt error data required for failure taxonomy and ablation studies. |

---

## Methodology

Design Science Research (Hevner et al., 2004) across four phases:

| Phase | Weeks | Key Activities |
|---|---|---|
| **Build** | 8-16 | DSL design, synthesis engine, verification module, integration adapters |
| **Demonstrate** | 17-28 | Dataset A + B construction, system integration, poster |
| **Evaluate** | 29-36 | Experiments, statistical analysis, ablation studies, failure taxonomy |
| **Communicate** | 37-40 | Dissertation, video demonstration, open-source release |

**Research methods:** Systematic literature review, document analysis, quasi-experimentation, statistical analysis (paired t-tests, Cohen's d), taxonomy development, case study analysis.

---

## Evaluation Design

**Primary metric:** pass@10 -- proportion of tasks where at least one correct workflow is generated within 10 attempts.

**Baselines (all on identical specs and test suites):**
- `baseline_pure_llm` -- single unconstrained LLM call (Claude Opus 4.6), no DSL constraint, no verification, no repair loop
- `baseline_langchain` -- a LangChain ReAct agent with tool access, no DSL constraint, no formal verification

**Ablation conditions (all against the `full` condition):**
- `no_verify` -- verification-gated retries removed
- `no_repair` -- repair loop removed (single attempt only)
- `no_taint` -- taint analysis removed from the Stage 1 verify/repair signal (the pytest suite's own taint test still runs, so a real violation still fails the task)

**Statistical analysis:** Paired t-tests, Cohen's d effect sizes, 95% confidence intervals, alpha = 0.05.

**Qualitative evaluation:** Failure mode taxonomy from `attempt_history` data.

**Security evaluation:** `security_pass_at_10` -- pass@10 restricted to tasks with `has_security_constraint: true`, targeting improvement beyond the 77% ceiling of prompt engineering alone (Aldosari & Aldawsari, 2026).

---

## Datasets

**Dataset A -- Enterprise Workflows**
133 real enterprise workflow synthesis tasks across 11 domains, from 20+ years of professional experience across financial services, healthcare, and manufacturing. Each task: natural language specification (`spec.md`) + reference DSL implementation (`reference_dsl.yaml`, documentation only -- not read by the evaluation code) + automated test suite (pytest). A fixed 60-task stratified sample (`scripts/dataset_a_sample.txt`) is used for the evaluation runs below.

**Dataset B -- Public Benchmarks**
60 tasks adapted from four public AI benchmarks: GAIA, WebArena, ToolLLM, AgentBench (see `datasets/dataset_b/README.md`).

---

## Results

Stored results from the final experiment run are in `results/session_09/` (120 tasks per condition: the 60-task Dataset A sample plus all 60 Dataset B tasks).

| Condition | pass@1 | pass@3 | pass@5 | pass@10 | mean attempts (success) | security_pass@10 |
|---|---|---|---|---|---|---|
| full | 60.83% | 80.83% | 85.00% | 88.33% | 1.64 | 90.38% (47/52) |
| no_repair | 62.50% | 62.50% | 62.50% | 62.50% | 1.00 | 57.69% |
| no_verify | 63.33% | 73.33% | 74.17% | 80.00% | 1.81 | 75.00% |
| no_taint | 65.00% | 86.67% | 88.33% | 90.00% | 1.50 | 94.23% (49/52) |
| baseline_pure_llm | 0% | 0% | 0% | 0% | -- | 0% |
| baseline_langchain | 5.15% (n=97) | 5.15% | 5.15% | 5.15% | 1.00 | 0% |

The `full` vs. `no_taint` difference is not statistically significant (p = 0.529); taint analysis's contribution is to security, not to pass@10. `baseline_langchain` is evaluated on 97/120 tasks -- the other 23 hit an Anthropic API billing failure during the original run and are excluded as infrastructure failures, not synthesis attempts.

Tracked API cost across all tracked conditions: $39.39 USD. This is an undercount -- `baseline_langchain` has a known token-tracking gap, and the real total spend for the full experiment (including failed/repeated runs) was approximately CA$250.

**Reproducing this analysis (no API key required, no network calls):**

```bash
python scripts/analyze_results.py
```

This reads the stored per-task JSON files in `results/session_09/` and reprints the full statistical analysis (the table above, plus by-complexity, by-domain, failure taxonomy, paired t-tests, and cost breakdown), overwriting `results/session_09/analysis_summary.json`.

---

## Key Literature

| Paper | Contribution to WorkflowSynth |
|---|---|
| Barke et al. (2024) HYSYNTH | Neural-symbolic synthesis baseline (58% vs 6% LLM-only). Validates hybrid architecture. |
| Tihanyi et al. (2025) ESBMC-AI | Verify-then-repair pattern. Formal feedback improves LLM repair from 31% to 80%+. |
| Tihanyi et al. (2025) FormAI-v2 | 62% of LLM programs contain vulnerabilities. Motivates verification module. |
| Xu et al. (2024) LLM4Workflow | Closest existing system. WorkflowSynth extends with formal verification. |
| Murphy et al. (2024) TSL+LLM | NL -> formal spec -> synthesis. Validates two-layer DSL design. |
| Aldosari & Aldawsari (2026) | Prompt engineering max 77% vuln reduction. Justifies formal verification. |
| Hevner et al. (2004) DSR | Design Science Research methodology. |
| Larsen et al. (2025) | DSR validity framework. Grounds evaluation design. |

---

## Implementation Status

| Component | Status | Unit tests | Test files |
|---|---|---|---|
| DSL Layer -- parser, AST, type checker | Complete | 20 | test_parser.py (12) + test_type_checker.py (8) |
| Verification Module -- taint analysis, evidence report | Complete | 33 | test_taint.py (14) + test_evidence_report.py (19) |
| Synthesis Engine -- LangGraph pipeline, prompts, LLM client | Complete | 31 | test_pipeline.py (19) + test_prompts.py (12) |
| Integration Layer -- n8n, LangChain adapters | Complete | 20 | test_integration.py (20) |
| Evaluation Module -- runner, baselines, metrics, ablation | Complete | 33 | test_evaluation.py (33) |
| **Total unit tests** | | **137** | `pytest tests/unit --collect-only -q` |

Plus 6 integration tests (`tests/integration/test_pipeline_e2e.py` (4) + `test_pipeline_diagnostic.py` (2)), which require `ANTHROPIC_API_KEY` and are skipped otherwise.

**Total tests passing: 143/143** (137 unit + 6 integration)

---

## Repository Structure

```
workflowsynth/
+-- docs/
|   +-- sessions/                        # Implementation session notes (01-09)
|   +-- APPENDIX_D_EXCERPTS.md            # Dissertation code/artefact excerpts
+-- src/
|   +-- dsl/
|   |   +-- constants.py                 # 25 VALID_OPS, type signatures
|   |   +-- ast_nodes.py                 # WorkflowStep, WorkflowAST dataclasses
|   |   +-- parser.py                    # YAML string -> WorkflowAST
|   |   +-- type_checker.py              # Type flow + auth rule verification
|   +-- synthesis/
|   |   +-- state.py                     # WorkflowSynthState TypedDict
|   |   +-- nodes.py                     # 7 LangGraph nodes
|   |   +-- pipeline.py                  # Graph definition + compile
|   |   +-- prompts.py                   # System + repair prompt templates
|   |   +-- llm_client.py                # Claude/GPT-5.4 client factory
|   +-- verification/
|   |   +-- taint.py                     # Taint analysis engine
|   |   +-- evidence_report.py           # Structured evidence report
|   +-- integration/                     # n8n + LangChain adapters
|   +-- evaluation/                      # Runner, baselines, metrics, ablation
+-- datasets/
|   +-- dataset_a/                       # 133 enterprise workflow tasks, 11 domains
|   +-- dataset_b/                       # 60 adapted public-benchmark tasks
+-- scripts/
|   +-- synthesize.py                    # Single-spec synthesis CLI
|   +-- run_evaluation.py                # Evaluation CLI (ablations + baselines)
|   +-- analyze_results.py               # Statistical analysis of stored results
|   +-- dataset_a_sample.txt             # The 60-task Dataset A evaluation sample
+-- results/
|   +-- session_09/                      # Final experiment results (6 conditions)
+-- examples/
|   +-- invoice_processing.md            # Demo spec for scripts/synthesize.py
+-- tests/
    +-- unit/                            # 137 tests, no API calls
    +-- integration/                     # 6 tests, require ANTHROPIC_API_KEY
```

---

## Academic Context

| | |
|---|---|
| **Institution** | University of Liverpool |
| **Programme** | MSc Artificial Intelligence |
| **Dissertation Advisor** | Kathleen Kelm |
| **Dissertation Lead** | Andrea Corradini |
| **Expected Completion** | 2 November 2026 |
| **Status** | Implementation and evaluation complete -- 143/143 tests passing |

