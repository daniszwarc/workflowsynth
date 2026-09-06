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
from workflowsynth.evaluation.baselines import LangChainAgentBaseline
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


# --- LangChainAgentBaseline ---------------------------------------------------

@pytest.fixture
def fake_task_dataset(tmp_path):
    """A fake dataset with one real task directory (spec.md + always-passing test)."""
    dataset_dir = tmp_path / "dataset_agent"
    dataset_dir.mkdir()
    index_yaml = textwrap.dedent(
        """
        dataset: dataset_agent
        version: "1.0"
        total_tasks: 1
        tasks:
          - {task_id: wf_agent_test_001, domain: general_ai, complexity: 1, has_security_constraint: false, primitive_count: 1}
        """
    )
    (dataset_dir / "index.yaml").write_text(index_yaml)

    task_dir = dataset_dir / "wf_agent_test_001"
    (task_dir / "tests").mkdir(parents=True)
    (task_dir / "spec.md").write_text("# Workflow: Trivial Task\n\nDo nothing of note.\n")
    (task_dir / "tests" / "test_wf_agent_test_001.py").write_text(
        "def test_always_passes(candidate_yaml):\n    assert candidate_yaml\n"
    )
    return dataset_dir


def test_langchain_agent_baseline_returns_task_result_on_success(fake_task_dataset, tmp_path, monkeypatch):
    baseline = LangChainAgentBaseline(
        dataset_path=str(fake_task_dataset),
        results_dir=str(tmp_path / "results"),
    )

    valid_yaml = "workflow_id: wf_agent_test_001\nsteps:\n  - id: s1\n    op: fetch_api\n"
    monkeypatch.setattr(baseline, "run_agent", lambda task_id, spec_text: valid_yaml)

    result = baseline.run_single("wf_agent_test_001")

    assert isinstance(result, TaskResult)
    assert result.condition == "langchain_agent_baseline"
    assert result.success is True
    assert result.failure_category == "success"
    assert result.attempts_used == 1


def test_langchain_agent_baseline_agent_error_on_invalid_yaml(fake_task_dataset, tmp_path, monkeypatch):
    baseline = LangChainAgentBaseline(
        dataset_path=str(fake_task_dataset),
        results_dir=str(tmp_path / "results"),
    )

    monkeypatch.setattr(baseline, "run_agent", lambda task_id, spec_text: "not: valid: yaml: [")

    result = baseline.run_single("wf_agent_test_001")

    assert result.success is False
    assert result.failure_category == "agent_error"

    # Same outcome when the agent raises outright instead of returning bad text.
    def raise_error(task_id, spec_text):
        raise RuntimeError("agent blew up")

    monkeypatch.setattr(baseline, "run_agent", raise_error)
    result = baseline.run_single("wf_agent_test_001")
    assert result.success is False
    assert result.failure_category == "agent_error"


def test_langchain_agent_baseline_tools_are_callable(fake_task_dataset, tmp_path):
    baseline = LangChainAgentBaseline(
        dataset_path=str(fake_task_dataset),
        results_dir=str(tmp_path / "results"),
    )

    tools = baseline.make_tools()
    names = {t.name for t in tools}
    assert names == {"search_primitives", "validate_yaml", "read_spec"}

    search_result = next(t for t in tools if t.name == "search_primitives").invoke({"query": "database"})
    assert isinstance(search_result, str)
    assert "read_database" in search_result and "write_database" in search_result

    validate_result = next(t for t in tools if t.name == "validate_yaml").invoke(
        {"yaml_str": "workflow_id: w\nsteps:\n  - id: s1\n    op: fetch_api\n"}
    )
    assert isinstance(validate_result, str)
    assert validate_result == "valid"

    invalid_validate_result = next(t for t in tools if t.name == "validate_yaml").invoke(
        {"yaml_str": "not: [valid"}
    )
    assert isinstance(invalid_validate_result, str)
    assert invalid_validate_result != "valid"

    spec_result = next(t for t in tools if t.name == "read_spec").invoke({"task_id": "wf_agent_test_001"})
    assert isinstance(spec_result, str)
    assert "Trivial Task" in spec_result


# --- Token usage tracking (Session 09) -----------------------------------------

def test_token_usage_in_attempt_record(fake_task_dataset, tmp_path, monkeypatch):
    runner = EvaluationRunner(
        dataset_path=str(fake_task_dataset),
        results_dir=str(tmp_path / "results"),
        condition="full",
    )

    class FakeResponse:
        content = "workflow_id: wf_agent_test_001\nsteps:\n  - id: s1\n    op: fetch_api\n"
        usage_metadata = {"input_tokens": 1000, "output_tokens": 500}

    class FakeLLM:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr("workflowsynth.evaluation.runner.get_llm", lambda attempt: FakeLLM())

    result = runner.run_single("wf_agent_test_001")

    assert result.attempt_history[0]["input_tokens"] == 1000
    assert result.attempt_history[0]["output_tokens"] == 500


def test_task_result_token_totals():
    result = make_result(
        total_input_tokens=1500,
        total_output_tokens=750,
        attempt_history=[
            {"attempt_number": 0, "success": False, "input_tokens": 1000, "output_tokens": 500},
            {"attempt_number": 1, "success": True, "input_tokens": 500, "output_tokens": 250},
        ],
    )
    assert result.total_input_tokens == 1500
    assert result.total_output_tokens == 750
    assert sum(a["input_tokens"] for a in result.attempt_history) == result.total_input_tokens
    assert sum(a["output_tokens"] for a in result.attempt_history) == result.total_output_tokens


def test_estimated_cost_calculation():
    from workflowsynth.evaluation.runner import _estimate_cost_usd

    assert _estimate_cost_usd(1_000_000, 1_000_000) == pytest.approx(30.0)


def test_batch_flag_cli():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/run_evaluation.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--batch" in result.stdout
