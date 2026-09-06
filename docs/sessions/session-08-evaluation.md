# WorkflowSynth -- Session 08: Evaluation Module

**Date:** September 6, 2026
**DSR Phase:** Evaluate
**Component:** Evaluation
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Implement the Evaluation Module (`src/evaluation/`) and run the pre-flight
validation on a representative 10-task sample from Dataset A.

---

## What was built

- `src/evaluation/runner.py` -- `EvaluationRunner`, `TaskResult`, `EvaluationSummary`
- `src/evaluation/metrics.py` -- `pass_at_k`, `mean_attempts`, `security_pass_rate`,
  `by_complexity`, `by_domain`, `summary_table`
- `src/evaluation/baselines.py` -- `PureLLMBaseline`, `SingleAttemptBaseline`
- `src/evaluation/ablation.py` -- `run_ablation` wrapper
- `scripts/run_evaluation.py` -- CLI entry point
- `tests/unit/test_evaluation.py` -- 21 tests
- `pyproject.toml` -- project dependency manifest, fixes Session 03 gap

---

## Key design decision

`run_pytest_suite()` in `runner.py` generates a temporary `conftest.py` that
injects the `candidate_yaml` fixture, then runs the dataset test suite in
an isolated subprocess per attempt. This was necessary because the
pipeline's `run_tests` node was a stub since Session 03.

---

## Pre-flight results (10-task sample)

7 of the 10 sampled tasks completed during pre-flight (the remaining 3 were
not run before the taint.py crash below halted the batch on `wf_cpl_004`,
which is not one of the 7 tracked here -- see Bug 1).

| task_id | success | attempts | category | complexity | domain | security | type_errors | taint_violations |
|---|---|---|---|---|---|---|---|---|
| wf_ae_001 | True | 3 | success | 2 | publishing | False | 2 | 1 |
| wf_btp_003 | False | 10 | test_failure | 4 | clinical_ai | True | 0 | 0 |
| wf_erd_006 | True | 2 | success | 4 | healthcare_billing | True | 2 | 0 |
| wf_mm_008 | True | 2 | success | 5 | clinical_ai | True | 1 | 0 |
| wf_ms_002 | True | 1 | success | 3 | clinical_ai | True | 0 | 0 |
| wf_mvp_003 | True | 10 | success | 5 | manufacturing | True | 9 | 0 |
| wf_pb_001 | True | 2 | success | 2 | insurance_brokerage | True | 2 | 0 |

Summary table (7 completed tasks, condition=full):

```
Evaluation summary -- condition: full
Total tasks: 7

Metric                       Value
----------------------------------
pass@1                      14.29%
pass@3                      71.43%
pass@5                      71.43%
pass@10                     85.71%
mean attempts (success)       3.33
security pass@10            83.33%

By complexity (pass@10):
  complexity 2              100.00%
  complexity 3              100.00%
  complexity 4               50.00%
  complexity 5              100.00%

By domain (pass@10):
  clinical_ai               66.67%
  healthcare_billing       100.00%
  insurance_brokerage      100.00%
  manufacturing            100.00%
  publishing               100.00%
```

---

## Bugs found and fixed

### Bug 1 -- taint.py unhashable type crash

`_process_step()` in `src/verification/taint.py` read
`step.params.get("input")` and directly checked `input_var in tainted_vars`.
On task `wf_cpl_004`, the LLM produced a candidate where `params.input` was
a nested dict rather than a string variable name (malformed but
structurally-valid-enough YAML to pass the parser). `dict in tainted_vars`
raised `TypeError: unhashable type: 'dict'`, and since `run_dataset` had no
per-task exception isolation at the time (see Bug 2), this crashed the
entire pre-flight batch.

Fix: `_process_step()` now checks `isinstance(input_var, str)` before doing
any membership test. A non-string `params.input` is treated as a taint
error in its own right -- it produces a `TaintViolation` with a message
telling the LLM exactly what shape `params.input` must have, and the step
is otherwise treated as having no input variable to check. This means a
non-string `input` is fed back into the repair loop as a structured
violation rather than crashing the whole evaluation. Full audit of the
function confirmed `params.get("input")` is the only params field ever
checked for taint-set membership; `step.output` is a typed AST attribute
(always a string or `None`), not a raw params value, so it does not need
the same guard.

### Bug 2 -- run_dataset exception propagation

`EvaluationRunner.run_dataset()` called `run_single()` directly, with no
exception handling. Any unhandled exception in one task (a crash in
verification, a bug in an adapter, a network error in the LLM client)
would abort the entire batch and lose all in-memory results for tasks that
had not yet been persisted. Given Dataset A has 133 tasks and Session 09
runs the full set across four conditions, a single bad task could throw
away hours of a run.

Fix: added `_run_single_safe()`, which wraps `run_single()` in a
try/except. On an unhandled exception it builds a failed `TaskResult`
(`success=False`, `failure_category="error"`, `attempts_used=0`,
`error_message=str(exception)`), persists it to
`results/{condition}/{task_id}.json` immediately, logs the error to
stderr, and lets `run_dataset` move on to the next task. `run_dataset` now
calls `_run_single_safe()` instead of `run_single()` in both the serial
and thread-pool paths. `TaskResult` gained a new `error_message: str = ""`
field (empty for normal runs, populated only on unhandled exceptions), and
`"error"` was added to the `FAILURE_CATEGORIES` vocabulary.

---

## Notable findings

### wf_ae_001 -- taint verification working correctly

The known missing `authenticate_user` / untainted `pdf_binary` issue was
detected by the taint analyser, fed back to the LLM as a structured repair
prompt, and corrected by attempt 3. Verification module confirmed working
on real LLM output.

### wf_btp_003 -- formally verified but functionally incorrect

Complexity 4, clinical_ai, security-constrained. Failed all 10 attempts.
Final attempts had zero type errors and zero taint violations -- the
output was DSL-valid and security-clean, but failed the functional tests.
This demonstrates the distinction between formal verification (structure
and security) and functional correctness (does it do what the spec says).
Worth a case study in the dissertation Discussion chapter.

### wf_mvp_003 -- complexity 5 at the attempt ceiling

Succeeded only on attempt 10 of 10, with 9 accumulated type errors along
the way. A legitimate pass, but indicates complexity-5 tasks are near the
difficulty ceiling for the current repair loop.

---

## Preliminary metrics (7 completed tasks)

```
Evaluation summary -- condition: full
Total tasks: 7

Metric                       Value
----------------------------------
pass@1                      14.29%
pass@3                      71.43%
pass@5                      71.43%
pass@10                     85.71%
mean attempts (success)       3.33
security pass@10            83.33%

By complexity (pass@10):
  complexity 2              100.00%
  complexity 3              100.00%
  complexity 4               50.00%
  complexity 5              100.00%

By domain (pass@10):
  clinical_ai               66.67%
  healthcare_billing       100.00%
  insurance_brokerage      100.00%
  manufacturing            100.00%
  publishing               100.00%
```

---

## Implementation Journal

```
Date: 2026-09-06
DSR Phase: Evaluate
Component: Evaluation
Type: Decision
Description: run_pytest_suite() runs dataset test suites in isolated
subprocesses with a dynamically generated conftest.py fixture.
Justification: The pipeline's run_tests node has been a stub since
Session 03. Real test execution is required for valid pass@10 measurement.
Subprocess isolation prevents test state leakage between attempts.
Dissertation Impact: Section 4 (Evaluation Design) -- grounds pass@10
in actual test execution rather than proxy metrics.
```

```
Date: 2026-09-06
DSR Phase: Evaluate
Component: Verification
Type: Failure
Description: taint.py crashed on wf_cpl_004 with TypeError: unhashable
type: 'dict' when LLM output contained a non-string params.input value.
Justification: Pre-flight testing revealed a latent bug never triggered
by hand-crafted test fixtures. Fixed by adding isinstance(input_var, str)
guard in _process_step().
Dissertation Impact: Section 5 (Discussion) -- illustrates the value of
real-LLM testing over synthetic test fixtures. Also a limitation: the
parser and type checker do not currently reject non-string param values
upstream of taint analysis.
```

---

## Next session

Session 09 -- Full Dataset A evaluation run (133 workflows, condition=full),
then ablation conditions (no_taint, no_repair, no_verify), then results
analysis and dissertation Section 4 write-up.
