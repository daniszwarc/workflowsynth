# tests/unit/test_evaluation.py
#
# Unit tests for the evaluation module (Session 08).
#
# NOTE: These tests do not invoke any LLM. EvaluationRunner.run_single and
# run_dataset require API keys and hit real dataset test suites -- that is
# exercised in the real experiment runs (Session 08, post-implementation),
# not here. These tests cover metrics math, index loading, and TaskResult
# serialisation.

import json
import textwrap

import pytest

from workflowsynth.evaluation.runner import EvaluationRunner, TaskResult, EvaluationSummary
from workflowsynth.evaluation.metrics import (
    pass_at_k,
    mean_attempts,
    security_pass_rate,
    by_complexity,
    by_domain,
    summary_table,
)


def make_result(**overrides) -> TaskResult:
    defaults = dict(
        task_id="wf_test_001",
        condition="full",
        success=True,
        attempts_used=1,
        pass_at_k={1: True, 3: True, 5: True, 10: True},
        dsl_type_errors=0,
        dsl_taint_violations=0,
        output_errors=0,
        failure_category="success",
        synthesis_time_seconds=1.23,
        attempt_history=[{"attempt_number": 0, "success": True}],
        complexity=2,
        domain="publishing",
        has_security_constraint=False,
    )
    defaults.update(overrides)
    return TaskResult(**defaults)


# --- pass_at_k ----------------------------------------------------------------

def test_pass_at_k_all_pass():
    results = [make_result(success=True, attempts_used=1) for _ in range(5)]
    assert pass_at_k(results, 1) == 1.0
    assert pass_at_k(results, 10) == 1.0


def test_pass_at_k_none_pass():
    results = [make_result(success=False, attempts_used=10) for _ in range(5)]
    assert pass_at_k(results, 1) == 0.0
    assert pass_at_k(results, 10) == 0.0


def test_pass_at_k_k_greater_than_attempts_used():
    # Succeeded on attempt 1 -- should count towards pass@10 even though
    # the run's own max_attempts might have been smaller than 10.
    results = [make_result(success=True, attempts_used=1)]
    assert pass_at_k(results, 10) == 1.0


def test_pass_at_k_partial_success_boundary():
    results = [
        make_result(task_id="a", success=True, attempts_used=1),
        make_result(task_id="b", success=True, attempts_used=5),
        make_result(task_id="c", success=False, attempts_used=10),
    ]
    assert pass_at_k(results, 1) == pytest.approx(1 / 3)
    assert pass_at_k(results, 3) == pytest.approx(1 / 3)
    assert pass_at_k(results, 5) == pytest.approx(2 / 3)
    assert pass_at_k(results, 10) == pytest.approx(2 / 3)


def test_pass_at_k_empty_results():
    assert pass_at_k([], 10) == 0.0


# --- mean_attempts --------------------------------------------------------------

def test_mean_attempts_only_over_successes():
    results = [
        make_result(task_id="a", success=True, attempts_used=2),
        make_result(task_id="b", success=True, attempts_used=4),
        make_result(task_id="c", success=False, attempts_used=10),
    ]
    assert mean_attempts(results) == pytest.approx(3.0)


def test_mean_attempts_no_successes():
    results = [make_result(success=False, attempts_used=10)]
    assert mean_attempts(results) == 0.0


# --- security_pass_rate ----------------------------------------------------------

def test_security_pass_rate_filters_non_security_tasks():
    results = [
        make_result(task_id="a", has_security_constraint=True, success=True, attempts_used=1),
        make_result(task_id="b", has_security_constraint=True, success=False, attempts_used=10),
        make_result(task_id="c", has_security_constraint=False, success=False, attempts_used=10),
    ]
    assert security_pass_rate(results) == pytest.approx(0.5)


def test_security_pass_rate_no_security_tasks():
    results = [make_result(has_security_constraint=False)]
    assert security_pass_rate(results) == 0.0


# --- by_complexity ----------------------------------------------------------------

def test_by_complexity_breakdown():
    results = [
        make_result(task_id="a", complexity=1, success=True, attempts_used=1),
        make_result(task_id="b", complexity=1, success=False, attempts_used=10),
        make_result(task_id="c", complexity=3, success=True, attempts_used=1),
    ]
    breakdown = by_complexity(results)
    assert breakdown == {1: pytest.approx(0.5), 3: pytest.approx(1.0)}


def test_by_complexity_empty_results():
    assert by_complexity([]) == {}


# --- by_domain ----------------------------------------------------------------

def test_by_domain_breakdown():
    results = [
        make_result(task_id="a", domain="publishing", success=True, attempts_used=1),
        make_result(task_id="b", domain="clinical_ai", success=False, attempts_used=10),
    ]
    breakdown = by_domain(results)
    assert breakdown == {"publishing": pytest.approx(1.0), "clinical_ai": pytest.approx(0.0)}


# --- summary_table ----------------------------------------------------------------

def test_summary_table_contains_key_metrics():
    results = [make_result()]
    table = summary_table(results)
    assert "pass@1" in table
    assert "pass@10" in table
    assert "full" in table


def test_summary_table_empty_results():
    assert "No results" in summary_table([])


# --- TaskResult JSON round-trip ------------------------------------------------

def test_task_result_json_round_trip():
    from dataclasses import asdict

    result = make_result(
        attempt_history=[
            {"attempt_number": 0, "dsl_type_errors": [], "dsl_taint_violations": [], "success": True}
        ]
    )
    serialised = json.dumps(asdict(result))
    restored = json.loads(serialised)

    assert restored["task_id"] == result.task_id
    assert restored["condition"] == result.condition
    assert restored["success"] == result.success
    assert restored["pass_at_k"] == {"1": True, "3": True, "5": True, "10": True}
    assert restored["attempt_history"] == result.attempt_history

    # Reconstructing from the round-tripped dict (with string-keyed pass_at_k
    # coerced back) should reproduce an equivalent TaskResult.
    restored["pass_at_k"] = {int(k): v for k, v in restored["pass_at_k"].items()}
    rebuilt = TaskResult(**restored)
    assert rebuilt == result


# --- EvaluationRunner index loading ------------------------------------------------

@pytest.fixture
def fake_dataset(tmp_path):
    dataset_dir = tmp_path / "dataset_a"
    dataset_dir.mkdir()
    index_yaml = textwrap.dedent(
        """
        dataset: dataset_a
        version: "1.0"
        total_tasks: 2
        tasks:
          - {task_id: wf_x_001, domain: publishing, complexity: 2, has_security_constraint: false, primitive_count: 5}
          - {task_id: wf_x_002, domain: clinical_ai, complexity: 4, has_security_constraint: true, primitive_count: 9}
        """
    )
    (dataset_dir / "index.yaml").write_text(index_yaml)
    return dataset_dir


def test_evaluation_runner_loads_index_yaml(fake_dataset, tmp_path):
    runner = EvaluationRunner(
        dataset_path=str(fake_dataset),
        results_dir=str(tmp_path / "results"),
        condition="full",
    )

    assert set(runner.task_ids) == {"wf_x_001", "wf_x_002"}
    assert runner.index["wf_x_001"]["domain"] == "publishing"
    assert runner.index["wf_x_001"]["complexity"] == 2
    assert runner.index["wf_x_001"]["has_security_constraint"] is False
    assert runner.index["wf_x_002"]["has_security_constraint"] is True


def test_evaluation_runner_creates_condition_results_dir(fake_dataset, tmp_path):
    results_dir = tmp_path / "results"
    EvaluationRunner(dataset_path=str(fake_dataset), results_dir=str(results_dir), condition="no_taint")
    assert (results_dir / "no_taint").is_dir()


def test_evaluation_runner_rejects_unknown_condition(fake_dataset, tmp_path):
    with pytest.raises(ValueError):
        EvaluationRunner(
            dataset_path=str(fake_dataset),
            results_dir=str(tmp_path / "results"),
            condition="not_a_real_condition",
        )


# --- run_dataset per-task exception isolation --------------------------------

def test_run_dataset_continues_past_task_that_raises(fake_dataset, tmp_path, monkeypatch):
    runner = EvaluationRunner(
        dataset_path=str(fake_dataset),
        results_dir=str(tmp_path / "results"),
        condition="full",
    )

    def fake_run_single(task_id):
        if task_id == "wf_x_001":
            raise RuntimeError("boom")
        return make_result(task_id=task_id, domain="clinical_ai", complexity=4, has_security_constraint=True)

    monkeypatch.setattr(runner, "run_single", fake_run_single)

    summary = runner.run_dataset()

    assert summary.total_tasks == 2


def test_run_dataset_failed_task_has_error_category_and_message(fake_dataset, tmp_path, monkeypatch):
    runner = EvaluationRunner(
        dataset_path=str(fake_dataset),
        results_dir=str(tmp_path / "results"),
        condition="full",
    )

    def fake_run_single(task_id):
        if task_id == "wf_x_001":
            raise RuntimeError("boom")
        return make_result(task_id=task_id)

    monkeypatch.setattr(runner, "run_single", fake_run_single)

    summary = runner.run_dataset()
    failed = next(r for r in summary.results if r.task_id == "wf_x_001")

    assert failed.success is False
    assert failed.failure_category == "error"
    assert failed.error_message == "boom"
    assert failed.attempts_used == 0

    persisted = json.loads((tmp_path / "results" / "full" / "wf_x_001.json").read_text())
    assert persisted["failure_category"] == "error"
    assert persisted["error_message"] == "boom"


def test_run_dataset_subsequent_tasks_still_complete_normally(fake_dataset, tmp_path, monkeypatch):
    runner = EvaluationRunner(
        dataset_path=str(fake_dataset),
        results_dir=str(tmp_path / "results"),
        condition="full",
    )

    def fake_run_single(task_id):
        if task_id == "wf_x_001":
            raise RuntimeError("boom")
        return make_result(task_id=task_id)

    monkeypatch.setattr(runner, "run_single", fake_run_single)

    summary = runner.run_dataset()
    ok_task = next(r for r in summary.results if r.task_id == "wf_x_002")

    assert ok_task.success is True
    assert ok_task.failure_category == "success"
    assert ok_task.error_message == ""
