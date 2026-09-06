# src/evaluation/runner.py
#
# The evaluation experiment runner. Drives WorkflowSynth (or an ablated
# variant of it) against Dataset A tasks, records per-attempt state, and
# persists results to disk immediately after each task completes.
#
# CONSTRAINT: attempt_history is append-only -- every attempt (successful
# or not) is appended once and never rewritten.
# CONSTRAINT: results are written to results/{condition}/{task_id}.json
# immediately after run_single() completes -- a crash mid-run must not
# lose already-completed results.

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml
from langchain_core.messages import SystemMessage, HumanMessage

from ..dsl.parser import parse_workflow
from ..dsl.type_checker import type_check
from ..verification.taint import taint_analysis
from ..synthesis.llm_client import get_llm
from ..synthesis.prompts import SYSTEM_PROMPT, build_repair_prompt

VALID_CONDITIONS = ("full", "no_taint", "no_repair", "no_verify")

# Allowed values for TaskResult.failure_category, per the Session 08 spec.
FAILURE_CATEGORIES = (
    "parse_error",
    "type_error",
    "taint_violation",
    "test_failure",
    "timeout",
    "success",
    "error",
    "agent_error",
)

DEFAULT_MAX_ATTEMPTS = 10
PYTEST_TIMEOUT_SECONDS = 60


# --- Dataclasses --------------------------------------------------------------

@dataclass
class TaskResult:
    task_id: str
    condition: str
    success: bool
    attempts_used: int
    pass_at_k: dict = field(default_factory=dict)
    dsl_type_errors: int = 0
    dsl_taint_violations: int = 0
    output_errors: int = 0
    failure_category: str = "test_failure"
    synthesis_time_seconds: float = 0.0
    attempt_history: list = field(default_factory=list)
    complexity: int = 0
    domain: str = ""
    has_security_constraint: bool = False
    error_message: str = ""


@dataclass
class EvaluationSummary:
    condition: str
    total_tasks: int
    pass_at_1: float
    pass_at_3: float
    pass_at_5: float
    pass_at_10: float
    mean_attempts: float
    security_pass_rate: float
    by_complexity: dict = field(default_factory=dict)
    by_domain: dict = field(default_factory=dict)
    results: list = field(default_factory=list)


# --- Pytest execution helper ---------------------------------------------------

class TestTimeoutError(Exception):
    """Raised when a task's pytest suite exceeds PYTEST_TIMEOUT_SECONDS."""


_CONFTEST_TEMPLATE = '''
import json
import pytest

CANDIDATE_YAML = {candidate_yaml!r}
_RESULTS_PATH = {results_path!r}


@pytest.fixture
def candidate_yaml():
    return CANDIDATE_YAML


_results = {{}}


def pytest_runtest_logreport(report):
    if report.when == "call":
        _results[report.nodeid] = report.outcome == "passed"
    elif report.when == "setup" and report.outcome != "passed":
        _results.setdefault(report.nodeid, False)


def pytest_sessionfinish(session, exitstatus):
    with open(_RESULTS_PATH, "w") as f:
        json.dump(_results, f)
'''


def run_pytest_suite(test_file: Path, candidate_yaml: str, timeout: int = PYTEST_TIMEOUT_SECONDS) -> dict:
    """
    Runs a Dataset A task's pytest suite against a candidate YAML string.

    The test files expect a `candidate_yaml` fixture (see
    datasets/dataset_a/*/tests/test_*.py). That fixture does not exist in
    the repo -- it is injected here via a generated conftest.py so each
    attempt can be tested against a different LLM-generated candidate
    without touching the dataset itself.

    Returns a dict of {{test_nodeid: bool}}. Raises TestTimeoutError if the
    suite does not finish within `timeout` seconds.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dest_test_file = tmp_path / test_file.name
        dest_test_file.write_text(test_file.read_text())

        results_path = tmp_path / "results.json"
        conftest_content = _CONFTEST_TEMPLATE.format(
            candidate_yaml=candidate_yaml,
            results_path=str(results_path),
        )
        (tmp_path / "conftest.py").write_text(conftest_content)

        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", str(dest_test_file), "-q", "--no-header"],
                cwd=str(tmp_path),
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TestTimeoutError(f"pytest suite for {test_file} exceeded {timeout}s") from exc

        if not results_path.exists():
            # The suite errored out before any report was written (e.g. a
            # collection error unrelated to the candidate). Treat as a
            # single failing "test".
            return {"collection_error": False}

        return json.loads(results_path.read_text())


# --- EvaluationRunner -----------------------------------------------------------

class EvaluationRunner:
    """
    Runs WorkflowSynth (or an ablated variant) against Dataset A tasks.

    `condition` controls which parts of verification/repair run:
        "full"      -- type checking + taint analysis + repair loop (10 attempts)
        "no_taint"  -- type checking only, taint analysis skipped, repair loop
        "no_repair" -- type checking + taint analysis, single attempt only
        "no_verify" -- no type checking, no taint analysis, repair loop
                       driven by test failures only. The DSL parser still
                       runs -- output must be valid YAML.
    """

    def __init__(self, dataset_path: str, results_dir: str, condition: str = "full"):
        if condition not in VALID_CONDITIONS:
            raise ValueError(f"Unknown condition {condition!r}. Must be one of {VALID_CONDITIONS}.")

        self.dataset_path = Path(dataset_path)
        self.results_dir = Path(results_dir)
        self.condition = condition

        self.index = self._load_index(self.dataset_path / "index.yaml")

        self._out_dir = self.results_dir / self.condition
        self._out_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_index(index_path: Path) -> dict:
        """Loads index.yaml into {task_id: {domain, complexity, has_security_constraint, ...}}."""
        with open(index_path) as f:
            raw = yaml.safe_load(f)

        index = {}
        for entry in raw.get("tasks", []):
            index[entry["task_id"]] = {
                "domain": entry.get("domain", ""),
                "complexity": entry.get("complexity", 0),
                "has_security_constraint": entry.get("has_security_constraint", False),
                "primitive_count": entry.get("primitive_count", 0),
            }
        return index

    @property
    def task_ids(self) -> list:
        return list(self.index.keys())

    # -- Public API ------------------------------------------------------------

    def run_dataset(self, max_workers: int = 1, task_ids: Optional[list] = None) -> EvaluationSummary:
        """
        Runs every task in `task_ids` (or the whole dataset if omitted),
        persisting each TaskResult immediately, then returns an
        EvaluationSummary computed from all completed results.
        """
        from .metrics import (
            pass_at_k as _pass_at_k,
            mean_attempts as _mean_attempts,
            security_pass_rate as _security_pass_rate,
            by_complexity as _by_complexity,
            by_domain as _by_domain,
        )

        ids = task_ids if task_ids is not None else self.task_ids
        results: list = []

        if max_workers <= 1:
            for task_id in ids:
                results.append(self._run_single_safe(task_id))
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self._run_single_safe, tid): tid for tid in ids}
                for future in as_completed(futures):
                    results.append(future.result())

        return EvaluationSummary(
            condition=self.condition,
            total_tasks=len(results),
            pass_at_1=_pass_at_k(results, 1),
            pass_at_3=_pass_at_k(results, 3),
            pass_at_5=_pass_at_k(results, 5),
            pass_at_10=_pass_at_k(results, 10),
            mean_attempts=_mean_attempts(results),
            security_pass_rate=_security_pass_rate(results),
            by_complexity=_by_complexity(results),
            by_domain=_by_domain(results),
            results=results,
        )

    def _run_single_safe(self, task_id: str) -> TaskResult:
        """
        Wraps run_single() so an unhandled exception on one task cannot
        abort the rest of the batch. On exception, builds a failed
        TaskResult, persists it, logs to stderr, and returns it.
        """
        try:
            return self.run_single(task_id)
        except Exception as exc:
            print(f"error: task {task_id!r} raised an unhandled exception: {exc}", file=sys.stderr)
            meta = self.index.get(task_id, {})
            result = TaskResult(
                task_id=task_id,
                condition=self.condition,
                success=False,
                attempts_used=0,
                failure_category="error",
                error_message=str(exc),
                complexity=meta.get("complexity", 0),
                domain=meta.get("domain", ""),
                has_security_constraint=meta.get("has_security_constraint", False),
            )
            self._persist(result)
            return result

    def run_single(self, task_id: str) -> TaskResult:
        """Runs the full synthesis + verification + test loop for one task."""
        start = time.monotonic()

        meta = self.index.get(task_id, {})
        spec_text = self._read_spec(task_id)
        test_file = self._test_file_path(task_id)

        max_attempts = 1 if self.condition == "no_repair" else DEFAULT_MAX_ATTEMPTS

        attempt_history: list = []
        success = False
        attempts_used = 0
        timed_out = False

        llm_sketch = self._translate_to_dsl(spec_text, attempt=0)

        for attempt_number in range(max_attempts):
            attempts_used = attempt_number + 1

            record = self._evaluate_attempt(attempt_number, llm_sketch, test_file)
            attempt_history.append(record)

            if record["success"]:
                success = True
                break

            if record["failure_category"] == "timeout":
                timed_out = True
                break

            is_last_attempt = attempt_number == max_attempts - 1
            if is_last_attempt:
                break

            llm_sketch = self._repair(
                original_spec=spec_text,
                failing_yaml=llm_sketch,
                record=record,
                attempt_number=attempt_number,
                max_attempts=max_attempts,
            )

        dsl_type_errors = sum(len(a["dsl_type_errors"]) for a in attempt_history)
        dsl_taint_violations = sum(len(a["dsl_taint_violations"]) for a in attempt_history)

        output_errors = 0
        if success:
            output_errors = self._check_output_layer(attempt_history[-1])

        if success:
            failure_category = "success"
        elif timed_out:
            failure_category = "timeout"
        else:
            failure_category = self._classify_task_failure(attempt_history)

        pass_at_k_map = {k: bool(success and attempts_used <= k) for k in (1, 3, 5, 10)}

        result = TaskResult(
            task_id=task_id,
            condition=self.condition,
            success=success,
            attempts_used=attempts_used,
            pass_at_k=pass_at_k_map,
            dsl_type_errors=dsl_type_errors,
            dsl_taint_violations=dsl_taint_violations,
            output_errors=output_errors,
            failure_category=failure_category,
            synthesis_time_seconds=time.monotonic() - start,
            attempt_history=attempt_history,
            complexity=meta.get("complexity", 0),
            domain=meta.get("domain", ""),
            has_security_constraint=meta.get("has_security_constraint", False),
        )

        self._persist(result)
        return result

    # -- Dataset I/O -------------------------------------------------------------

    def _read_spec(self, task_id: str) -> str:
        return (self.dataset_path / task_id / "spec.md").read_text()

    def _test_file_path(self, task_id: str) -> Path:
        return self.dataset_path / task_id / "tests" / f"test_{task_id}.py"

    def _persist(self, result: TaskResult) -> None:
        out_path = self._out_dir / f"{result.task_id}.json"
        out_path.write_text(json.dumps(asdict(result), indent=2))

    # -- Synthesis / verification -------------------------------------------------

    def _translate_to_dsl(self, spec_text: str, attempt: int) -> str:
        llm = get_llm(attempt)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=spec_text),
        ]
        response = llm.invoke(messages)
        return response.content.strip()

    def _repair(self, original_spec, failing_yaml, record, attempt_number, max_attempts) -> str:
        repair_prompt = build_repair_prompt(
            original_spec=original_spec,
            failing_yaml=failing_yaml,
            type_errors=record["dsl_type_errors"],
            taint_violations=record["dsl_taint_violations"],
            test_failures=record["test_results"],
            attempt_number=attempt_number,
            max_attempts=max_attempts,
        )
        llm = get_llm(attempt_number + 1)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=repair_prompt),
        ]
        response = llm.invoke(messages)
        return response.content.strip()

    def _verify(self, ast) -> tuple:
        """Returns (type_errors, taint_violations) according to self.condition."""
        if self.condition == "no_verify":
            return [], []

        type_errors = type_check(ast)

        if self.condition == "no_taint":
            return type_errors, []

        taint_violations = [v.message for v in taint_analysis(ast)]
        return type_errors, taint_violations

    def _evaluate_attempt(self, attempt_number: int, llm_sketch: str, test_file: Path) -> dict:
        """
        Runs parse -> verify -> test for a single attempt candidate.
        Returns a fully-populated attempt record (append-only unit).
        """
        parse_result = parse_workflow(llm_sketch)

        if not parse_result["ok"]:
            return {
                "attempt_number": attempt_number,
                "llm_sketch": llm_sketch,
                "dsl_type_errors": parse_result["errors"],
                "dsl_taint_violations": [],
                "test_results": {},
                "failure_category": "parse_error",
                "success": False,
            }

        ast = parse_result["ast"]
        type_errors, taint_violations = self._verify(ast)
        verification_passed = not type_errors and not taint_violations

        test_results: dict = {}
        if verification_passed:
            try:
                test_results = run_pytest_suite(test_file, llm_sketch)
            except TestTimeoutError:
                return {
                    "attempt_number": attempt_number,
                    "llm_sketch": llm_sketch,
                    "dsl_type_errors": type_errors,
                    "dsl_taint_violations": taint_violations,
                    "test_results": {},
                    "failure_category": "timeout",
                    "success": False,
                }

        tests_passed = bool(test_results) and all(test_results.values())
        success = verification_passed and tests_passed

        if success:
            category = "success"
        elif type_errors:
            category = "type_error"
        elif taint_violations:
            category = "taint_violation"
        else:
            category = "test_failure"

        return {
            "attempt_number": attempt_number,
            "llm_sketch": llm_sketch,
            "dsl_type_errors": type_errors,
            "dsl_taint_violations": taint_violations,
            "test_results": test_results,
            "failure_category": category,
            "success": success,
        }

    def _check_output_layer(self, final_record: dict) -> int:
        """
        Runs the integration layer (n8n + LangChain adapters) against the
        winning candidate and counts errors raised during translation.
        """
        from ..dsl.ast_nodes import WorkflowAST, WorkflowStep
        from ..verification.evidence_report import generate_evidence_report
        from ..integration.n8n_adapter import to_n8n_json
        from ..integration.langchain_adapter import to_langchain_python

        parse_result = parse_workflow(final_record["llm_sketch"])
        if not parse_result["ok"]:
            return 1

        ast = parse_result["ast"]
        errors = 0

        try:
            report = generate_evidence_report(
                ast=ast,
                synthesis_attempts=final_record["attempt_number"] + 1,
                type_errors=final_record["dsl_type_errors"],
                taint_violations=final_record["dsl_taint_violations"],
                test_results=final_record["test_results"],
            )
            to_n8n_json(ast, report)
            to_langchain_python(ast, report)
        except Exception:
            errors += 1

        return errors

    @staticmethod
    def _classify_task_failure(attempt_history: list) -> str:
        """
        Classifies the overall task failure from the full attempt history,
        restricted to the allowed failure_category vocabulary.
        """
        if not attempt_history:
            return "test_failure"

        from collections import Counter

        categories = [a["failure_category"] for a in attempt_history if a["failure_category"] != "success"]
        if not categories:
            return "test_failure"
        return Counter(categories).most_common(1)[0][0]
