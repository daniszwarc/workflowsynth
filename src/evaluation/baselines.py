# src/evaluation/baselines.py
#
# Baseline runners compared against full WorkflowSynth. Both produce the
# same TaskResult schema as EvaluationRunner so metrics.py works unchanged
# across baselines and the main system.

from dataclasses import asdict
import json
import time
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from ..dsl.parser import parse_workflow
from ..synthesis.llm_client import get_llm
from .runner import EvaluationRunner, TaskResult, TestTimeoutError, run_pytest_suite

# Deliberately generic -- no DSL vocabulary, no hard constraints, no
# verification hints. This is what "no DSL, no verification" means in
# practice: the LLM gets the spec and nothing else.
_PURE_LLM_PROMPT = """You are an assistant that designs enterprise workflows.

Given a natural language description, produce a YAML workflow with a
`workflow_id` field and a `steps` list. Each step should have an `id`,
an `op` describing the action, optional `params`, and optional `output`.

Respond with ONLY the YAML. No explanation, no markdown fences."""


class PureLLMBaseline:
    """
    Generates workflows with Claude Opus directly from the spec -- no DSL
    constraints, no verification, no repair loop. Single attempt only.
    Tests the raw output directly against the task's pytest suite.
    """

    def __init__(self, dataset_path: str, results_dir: str):
        self.dataset_path = Path(dataset_path)
        self.results_dir = Path(results_dir)
        self.condition = "pure_llm_baseline"
        self.index = EvaluationRunner._load_index(self.dataset_path / "index.yaml")

        self._out_dir = self.results_dir / self.condition
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def run_single(self, task_id: str, spec_text: str = None) -> TaskResult:
        start = time.monotonic()
        meta = self.index.get(task_id, {})

        if spec_text is None:
            spec_text = (self.dataset_path / task_id / "spec.md").read_text()
        test_file = self.dataset_path / task_id / "tests" / f"test_{task_id}.py"

        llm = get_llm(0)
        messages = [
            SystemMessage(content=_PURE_LLM_PROMPT),
            HumanMessage(content=spec_text),
        ]
        response = llm.invoke(messages)
        raw_output = response.content.strip()

        parse_result = parse_workflow(raw_output)

        if not parse_result["ok"]:
            record = {
                "attempt_number": 0,
                "llm_sketch": raw_output,
                "dsl_type_errors": parse_result["errors"],
                "dsl_taint_violations": [],
                "test_results": {},
                "failure_category": "parse_error",
                "success": False,
            }
        else:
            test_results = {}
            failure_category = "test_failure"
            success = False
            try:
                test_results = run_pytest_suite(test_file, raw_output)
                success = bool(test_results) and all(test_results.values())
                if success:
                    failure_category = "success"
            except TestTimeoutError:
                failure_category = "timeout"

            record = {
                "attempt_number": 0,
                "llm_sketch": raw_output,
                "dsl_type_errors": [],
                "dsl_taint_violations": [],
                "test_results": test_results,
                "failure_category": failure_category,
                "success": success,
            }

        success = record["success"]
        result = TaskResult(
            task_id=task_id,
            condition=self.condition,
            success=success,
            attempts_used=1,
            pass_at_k={k: success for k in (1, 3, 5, 10)},
            dsl_type_errors=len(record["dsl_type_errors"]),
            dsl_taint_violations=0,
            output_errors=0,
            failure_category=record["failure_category"],
            synthesis_time_seconds=time.monotonic() - start,
            attempt_history=[record],
            complexity=meta.get("complexity", 0),
            domain=meta.get("domain", ""),
            has_security_constraint=meta.get("has_security_constraint", False),
        )

        (self._out_dir / f"{task_id}.json").write_text(json.dumps(asdict(result), indent=2))
        return result


class SingleAttemptBaseline:
    """
    Runs WorkflowSynth with max_attempts=1 (no repair loop). Equivalent to
    the "no_repair" ablation condition -- kept as an explicit baseline class
    so experiment scripts can name it directly.
    """

    def __init__(self, dataset_path: str, results_dir: str):
        self._runner = EvaluationRunner(dataset_path, results_dir, condition="no_repair")

    def run_single(self, task_id: str, spec_text: str = None) -> TaskResult:
        return self._runner.run_single(task_id)
