# Dataset B -- Benchmark-Inspired Workflow Synthesis Tasks

60 workflow synthesis tasks inspired by four established agent evaluation
benchmarks, adapted to the WorkflowSynth 25-primitive DSL. Where Dataset A
draws on real enterprise workflows, Dataset B tests WorkflowSynth against
task shapes drawn from the broader agent-benchmarking literature -- multi-tool
reasoning, web task automation, REST API chaining, and general agent tasks.

## Structure

Each task directory contains:
- `spec.md` -- Natural language specification (LLM input only)
- `reference_dsl.yaml` -- Reference DSL implementation (ground truth, never shown to LLM)
- `tests/test_{wf_id}.py` -- Pytest suite verifying candidate correctness

## Benchmark Breakdown

| Domain | Prefix | Inspired by | Count | Security tasks |
|---|---|---|---|---|
| General AI | wf_gaia | GAIA | 15 | 6 |
| Web Automation | wf_web | WebArena | 15 | 6 |
| API Integration | wf_tool | ToolLLM | 15 | 6 |
| Agent Tasks | wf_agent | AgentBench | 15 | 6 |
| **Total** | | | **60** | **24** |

## Complexity Distribution

| Benchmark | Complexity 1 | Complexity 2 | Complexity 3 | Complexity 4 | Complexity 5 |
|---|---|---|---|---|---|
| wf_gaia | 5 | 4 | 3 | 2 | 1 |
| wf_web | 3 | 4 | 4 | 3 | 1 |
| wf_tool | 3 | 4 | 4 | 3 | 1 |
| wf_agent | 3 | 3 | 4 | 3 | 2 |

## Design Notes

- Every `reference_dsl.yaml` step uses only ops from `VALID_OPS`
  (`src/dsl/constants.py`). No invented operators.
- Every reference implementation was verified to pass `type_check()` and
  `taint_analysis()` with zero errors/violations, and to pass its own test
  suite (used as a stand-in `candidate_yaml`) before being committed.
- `has_security_constraint: true` marks tasks that involve `authenticate_user`,
  `encrypt_field`, or `log_audit` on sensitive data -- roughly 40% of each
  benchmark group, matching the security-task proportion in Dataset A.
- Test suites verify structural and semantic properties of a candidate
  (parses, type-checks, passes taint analysis, contains/orders the expected
  ops) -- they never compare a candidate against `reference_dsl.yaml`
  directly, since the LLM is expected to produce a structurally different
  but behaviourally equivalent workflow.

## Anonymization

Not applicable -- all Dataset B tasks are synthetic, modeled on the public
task descriptions of GAIA, WebArena, ToolLLM, and AgentBench rather than on
any real client work.
