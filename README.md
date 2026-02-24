# WorkflowSynth

> **MSc Capstone Research — Automated Discovery of Enterprise AI Workflows via LLM-Guided Programme Synthesis**
> University of Liverpool · MSc Artificial Intelligence · Jan 2024 – Nov 2026

---

## Research Overview

Enterprise AI adoption is constrained not by model capability, but by the difficulty of translating business requirements into reliable, production-grade AI workflows. WorkflowSynth investigates whether LLMs can be used to automatically discover, synthesize, and validate AI workflow definitions from natural language business requirements — reducing the engineering effort required to deploy AI in operational contexts.

---

## Research Question

> *To what extent can LLM-guided programme synthesis automatically generate correct, reliable, and reusable enterprise AI workflow definitions from structured business requirements?*

---

## Core Concepts

### Programme Synthesis
The automated generation of executable programs from high-level specifications. WorkflowSynth applies this to AI workflow definitions — treating n8n workflow JSON (or equivalent) as the target "programme" to be synthesized.

### LLM-Guided Search
Rather than exhaustive search over workflow space, the system uses an LLM to propose, evaluate, and refine workflow candidates based on requirement matching, tool availability, and reliability constraints.

### Workflow Validation
Synthesized workflows are validated against a prototype execution environment to verify correctness before being proposed to the user.

---

## Proposed Architecture

```
Natural Language
Business Requirements
        │
        ▼
┌──────────────────────┐
│  Requirement Parser  │  Extracts: trigger, tools needed,
│  (LLM)               │  data flow, output constraints
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Workflow Synthesizer│  LLM proposes workflow structure
│  (LangGraph)         │  as graph of nodes + edges
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Prototype Validator │  Executes workflow in sandboxed
│  (n8n)               │  n8n environment, checks output
└──────────┬───────────┘
           │
       Pass / Fail
           │
           ▼
┌──────────────────────┐
│  Refinement Loop     │  LLM revises based on failure
│  (CRAG-inspired)     │  feedback — up to N iterations
└──────────────────────┘
```

---

## Methodology

The research follows a design science methodology:

1. **Literature review** — programme synthesis, LLM code generation, AI workflow orchestration, enterprise automation
2. **Prototype development** — LangGraph-based synthesis engine + n8n validation environment
3. **Evaluation** — benchmark suite of business requirement → workflow pairs, scored on correctness, reliability, and generalizability
4. **Analysis** — where does LLM-guided synthesis succeed and fail, and why?

---

## Repository Structure

```
workflowsynth/
├── research/
│   ├── proposal.md          # Full dissertation proposal
│   ├── literature/          # Annotated bibliography
│   └── methodology.md       # Detailed research design
├── prototype/
│   ├── synthesizer/         # LangGraph synthesis engine
│   ├── validator/           # n8n workflow validator
│   └── benchmarks/          # Evaluation test cases
└── docs/
    └── architecture.md      # System design documentation
```

---

## Stack

| Component | Technology |
|---|---|
| Synthesis Engine | LangGraph, LangChain |
| LLM | Claude API (Anthropic) |
| Validation Environment | n8n (self-hosted) |
| Language | Python |
| Research Tools | Academic Paper Annotator (custom n8n pipeline) |

---

## Status

**Active research** — Dissertation deadline: November, 2026

- [ ] Proposal submitted
- [ ] Literature review in progress
- [ ] Architecture designed
- [ ] Prototype implementation
- [ ] Evaluation benchmarks
- [ ] Dissertation writeup

---

## Academic Context

**Institution:** University of Liverpool
**Programme:** MSc Artificial Intelligence
**Supervisor:** Kathleen Kelm
**Expected Completion:** November 2026

---

## Related Projects

- [Soccer Verdun AI Support](https://github.com/danisola/soccer-verdun-ai) — production multi-tool RAG agent (practical application of agentic patterns studied in this research)
- [AlterEco Publishing Pipeline](https://github.com/danisola/altereco-pipeline) — production document intelligence pipeline
