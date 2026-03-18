# WorkflowSynth

> **MSc AI Capstone — Automated Generation of Correct and Secure Enterprise Workflows via LLM-Guided Programme Synthesis and Formal Verification**
> University of Liverpool · MSc Artificial Intelligence · Jan 2026 – Nov 2026

---

## Research Question

**Primary:**
> To what extent can combining LLM-guided programme synthesis with formal verification improve the automatic generation of correct and secure enterprise-grade workflows from natural language specifications, compared to unconstrained LLM generation?

**Secondary:**
> 1. **Correctness:** How effectively does sketch-guided synthesis constrain the LLM search space to reduce hallucination while preserving the expressiveness needed for real enterprise workflow patterns?
> 2. **Security:** Can lightweight formal verification — specifically type safety checking and taint analysis — detect and eliminate security vulnerabilities in synthesised enterprise workflows without requiring full theorem-proving infrastructure?
> 3. **Viability:** How does WorkflowSynth's hybrid neural-symbolic approach compare to existing state-of-the-art baselines in enterprise workflow automation?

---

## The Problem

Enterprise workflow development consumes 60–80% of IT budgets ($85B annually in the US). LLMs can generate workflows rapidly but cannot guarantee correctness or security in production — 62% of LLM-generated programs contain formally verified vulnerabilities (Tihanyi et al., 2025). Prompt engineering alone achieves at most 77% vulnerability reduction (Aldosari & Aldawsari, 2026), which is insufficient for enterprise deployment. WorkflowSynth addresses this gap by combining LLM generation with formal verification in a single integrated pipeline.

---

## System Architecture

WorkflowSynth is a Python-based system with four components forming a sequential pipeline:

```
Natural Language Specification (SKILL.md format)
                    │
                    ▼
    ┌───────────────────────────────┐
    │       SYNTHESIS ENGINE        │
    │   LangGraph + LangChain       │
    │                               │
    │  LLM translates spec → DSL    │
    │  Iterative verify-then-repair │
    │  loop (max 10 attempts)       │
    └──────────────┬────────────────┘
                   │
                   ▼
    ┌───────────────────────────────┐
    │          DSL LAYER            │
    │     Python + Lark parser      │
    │                               │
    │  Formal YAML-based internal   │
    │  representation               │
    │  25 constrained primitives    │
    │  Type system enforcement      │
    └──────────────┬────────────────┘
                   │
                   ▼
    ┌───────────────────────────────┐
    │     VERIFICATION MODULE       │
    │       Custom Python           │
    │                               │
    │  Stage 1: DSL-level           │
    │  - Type safety checker        │
    │  - Taint analysis engine      │
    │                               │
    │  Stage 2: Output-level        │
    │  - n8n JSON validation        │
    │  - LangChain Python checks    │
    └──────────────┬────────────────┘
                   │
                   ▼
    ┌───────────────────────────────┐
    │      INTEGRATION LAYER        │
    │     Python serialisers        │
    │                               │
    │  n8n JSON adapter             │
    │  LangChain Python adapter     │
    └───────────────────────────────┘
```

---

## LangGraph Pipeline

The synthesis engine uses a stateful LangGraph pipeline implementing the verify-then-repair loop:

```
[START]
   │
   ▼
[translate_to_dsl]     LLM translates NL spec to YAML DSL candidate
   │
   ▼
[verify_dsl]           Type safety + taint analysis on DSL
   │
   ▼
[run_tests]            Execute candidate against test suite
   │
   ▼
[check_pass_or_repair] Decision node
   │                        │                        │
   ▼ (pass)                 ▼ (fail, attempts < 10)  ▼ (fail, attempts == 10)
[translate_output]     [repair_with_llm]         [record_failure]
   │                        │                        │
   ▼                        └──────→ [verify_dsl]    ▼
[verify_output]                                  [END — failure]
   │
   ▼
[END — success]
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
| Primary LLMs | Claude + GPT-5.4 | Swappable via LangChain abstraction |
| Testing | pytest | Standard Python testing |

---

## DSL — 25 Primitives

The formal vocabulary WorkflowSynth generates. No operations outside this list may be synthesised.

**Data Operations (8):** `fetch_api` `filter_records` `transform_json` `validate_schema` `aggregate_data` `merge_datasets` `extract_field` `format_output`

**Control Flow (8):** `route_to_step` `apply_rule` `loop_records` `parallel_execute` `wait_for_condition` `handle_error` `retry_step` `terminate_workflow`

**Integration Operations (9):** `send_to_queue` `log_audit` `notify_user` `call_webhook` `read_database` `write_database` `authenticate_user` `encrypt_field` `call_subworkflow`

---

## Key Architectural Decisions

| Decision | Choice | Justification |
|---|---|---|
| DSL Input Format | Two-layer: SKILL.md NL input → formal YAML DSL internally | Separates human-friendly interface from formally verifiable representation. Based on Murphy et al. (2024). |
| Synthesis Search | LLM-guided iterative refinement, max 10 attempts | Verify-then-repair pattern (Tihanyi et al., 2025). Bottom-up enumeration rejected as impractical for enterprise workflows. |
| Verification Scope | Two-stage: DSL-level + output-level | DSL-only rejected — cannot detect vulnerabilities introduced during translation. |
| Pipeline State | Full state object, append-only attempt history | Minimal state rejected — per-attempt error data required for failure taxonomy and ablation studies. |

---

## Methodology

Design Science Research (Hevner et al., 2004) across four phases:

| Phase | Weeks | Key Activities |
|---|---|---|
| **Build** | 8–16 | DSL design, synthesis engine, verification module, integration adapters |
| **Demonstrate** | 17–28 | Dataset A + B construction, system integration, poster |
| **Evaluate** | 29–36 | Experiments, statistical analysis, ablation studies, failure taxonomy |
| **Communicate** | 37–40 | Dissertation, video demonstration, open-source release |

**Research methods:** Systematic literature review, document analysis, quasi-experimentation, statistical analysis (paired t-tests, Cohen's d), taxonomy development, case study analysis.

---

## Evaluation Design

**Primary metric:** pass@10 — proportion of tasks where at least one correct workflow is generated within 10 attempts.

**Baselines (all on identical specs and test suites):**
- Pure LLM generation (GPT-5.4, no DSL constraint, no verification)
- LangChain agents
- Manual implementations

**Ablation conditions:**
- Full WorkflowSynth system
- No verification
- No LLM sketches
- No synthesis search (single attempt)

**Statistical analysis:** Paired t-tests, Cohen's d effect sizes, 95% confidence intervals, α = 0.05.

**Qualitative evaluation:** Failure mode taxonomy, two case studies (most complex successful synthesis, largest performance gap vs baseline).

**Security evaluation:** Vulnerability reduction rate across SQL injection, command injection, and data leakage, targeting improvement beyond the 77% ceiling of prompt engineering alone (Aldosari & Aldawsari, 2026).

---

## Datasets

**Dataset A — Enterprise Workflows**
120–150 real enterprise workflow synthesis tasks from 20+ years of professional experience across financial services, healthcare, and manufacturing. Each task: natural language specification (markdown) + reference DSL implementation (YAML) + automated test suite (pytest).

**Dataset B — Public Benchmarks**
Four public AI benchmarks adapted to WorkflowSynth DSL: GAIA, WebArena, ToolBench, AgentBench.

---

## Key Literature

| Paper | Contribution to WorkflowSynth |
|---|---|
| Barke et al. (2024) HYSYNTH | Neural-symbolic synthesis baseline (58% vs 6% LLM-only). Validates hybrid architecture. |
| Tihanyi et al. (2025) ESBMC-AI | Verify-then-repair pattern. Formal feedback improves LLM repair from 31% → 80%+. |
| Tihanyi et al. (2025) FormAI-v2 | 62% of LLM programs contain vulnerabilities. Motivates verification module. |
| Xu et al. (2024) LLM4Workflow | Closest existing system. WorkflowSynth extends with formal verification. |
| Murphy et al. (2024) TSL+LLM | NL → formal spec → synthesis. Validates two-layer DSL design. |
| Aldosari & Aldawsari (2026) | Prompt engineering max 77% vuln reduction. Justifies formal verification. |
| Hevner et al. (2004) DSR | Design Science Research methodology. |
| Larsen et al. (2025) | DSR validity framework. Grounds evaluation design. |

---

## University Milestones

| Week | Date | Milestone | Weight | Current Status |
|---|---|---|---|---|
| 8 | 23 Mar 2026 | Proposal Approval | 10% | **Approved**
| 11 | 13 Apr 2026 | Ethical Approval Submission | — |---|
| 16 | 18 May 2026 | Specification & Design Report | 10% |---|
| 28 | 10 Aug 2026 | Poster | 10% |---|
| 36 | 5 Oct 2026 | Draft Submission | — |---|
| 40 | 2 Nov 2026 | IT Artefact + Video Demo + Dissertation | 70% |---|

---

## Repository Structure

```
workflowsynth/
├── SKILL.md                    # Claude Code skill — read before implementation
├── research/
│   ├── proposal/               # Approved proposal (v5)
│   ├── spec_design_report/     # Specification & Design Report
│   ├── literature/             # 20 annotated sources across 5 categories
│   └── journal/                # Implementation decision log
├── src/
│   ├── dsl/                    # DSL grammar (Lark) + parser
│   ├── synthesis/              # LangGraph pipeline + LLM orchestration
│   ├── verification/           # Type safety checker + taint analyser
│   └── integration/            # n8n adapter + LangChain adapter
├── datasets/
│   ├── dataset_a/              # Enterprise workflow synthesis tasks
│   └── dataset_b/              # Adapted public benchmarks
├── evaluation/
│   ├── experiments/            # Experiment scripts
│   ├── baselines/              # Baseline implementations
│   └── results/                # Raw results + statistical analysis
└── tests/
    ├── unit/                   # Component unit tests
    └── integration/            # End-to-end pipeline tests
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
| **Status** | Proposal approved — Build phase in progress |

---

## Related Projects

- [Soccer Verdun AI Support](https://github.com/daniszwarc/soccer-verdun-ai) — production multilingual RAG agent
- [AlterEco Publishing Pipeline](https://github.com/daniszwarc/altereco-pipeline) — production PDF-to-Drupal automation pipeline
