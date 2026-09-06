# Session 09 -- Full Experiment Run

**Date:** 2026-09-06
**DSR Phase:** Evaluate
**Week:** 35 (of 40)

## Objective

Run the complete WorkflowSynth evaluation experiment across both datasets
and all conditions. Produce the quantitative results needed for
dissertation Section 4 (Evaluation Results) and Section 5 (Discussion).

Specific goals:
1. Implement Batch API support and token usage tracking (cost management)
2. Run condition=full on Dataset A (133 tasks) -- primary result
3. Run condition=full on Dataset B (60 tasks) -- generalization result
4. Run all ablation conditions (no_verify, no_repair, no_taint) on both datasets
5. Run all baselines (PureLLMBaseline, LangChainAgentBaseline) on both datasets
6. Compute statistical analysis: pass@10, mean_attempts, security_pass_rate,
   by_complexity, by_domain, paired t-tests, Cohen's d, 95% CIs
7. Build failure taxonomy from attempt_history data
8. Write two case studies: most complex successful synthesis + largest
   performance gap against a baseline
9. Commit all results and analysis

## Primary metric

pass@10: fraction of tasks where WorkflowSynth generates a correct,
verified workflow within 10 attempts.

Target: exceed 58% (Barke et al., 2024) and 52.7% (Wei et al., 2025).

## Conditions to run

| Condition | Description | Dataset A | Dataset B |
|---|---|---|---|
| full | WorkflowSynth complete pipeline | 133 tasks | 60 tasks |
| no_verify | Skip type check + taint analysis | 133 tasks | 60 tasks |
| no_repair | Single attempt, no repair loop | 133 tasks | 60 tasks |
| no_taint | Skip taint analysis only | 133 tasks | 60 tasks |
| baseline_pure_llm | Pure LLM, no DSL, no verification | 133 tasks | 60 tasks |
| baseline_langchain | LangChain ReAct agent | 133 tasks | 60 tasks |

Total: 193 tasks × 6 conditions = 1,158 task runs

## Budget

Available: CA$94.75 (~USD$70)
Strategy: Batch API for first attempts (50% discount), synchronous
for repair attempts (sequentially dependent).
Estimated cost: ~USD$50-60 for full experiment.

## What was built this session

(To be filled in as work completes)

## Experiment results

(To be filled in after runs complete)

## Statistical analysis

(To be filled in after runs complete)

## Failure taxonomy

(To be filled in after runs complete)

## Case studies

(To be filled in after runs complete)

## Implementation journal entries

(To be filled in as work completes)

## Next session

Session 10 -- Draft Submission preparation (Week 36, due 5 October 2026).
Write dissertation sections: Introduction, Literature Review, Methodology,
Evaluation Results, Discussion, Conclusion.
