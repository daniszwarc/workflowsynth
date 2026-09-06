# src/evaluation/baselines.py
#
# Baseline runners compared against full WorkflowSynth. Both produce the
# same TaskResult schema as EvaluationRunner so metrics.py works unchanged
# across baselines and the main system.

from dataclasses import asdict
import json
import time
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

from ..dsl.constants import VALID_OPS
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


# --- LangChain agent baseline -------------------------------------------------
#
# Deliberately generic ReAct-style agent: no WorkflowSynth DSL enforcement,
# no type checking, no taint analysis. It has *awareness* of the DSL
# vocabulary via search_primitives, and can self-check YAML syntax via
# validate_yaml, but nothing stops it from producing structurally invalid
# or unsafe output. Single attempt only -- no repair loop.

_AGENT_SYSTEM_PROMPT = """You are an assistant that designs enterprise workflows.

You have three tools available:
- search_primitives(query): look up which of WorkflowSynth's valid DSL
  operators match a keyword, for inspiration. You are not required to use
  only these operators.
- validate_yaml(yaml_str): check whether a YAML string parses as a valid
  workflow (has a workflow_id and a steps list with id/op per step).
- read_spec(task_id): re-read the natural language specification for a
  task, if you need to refer back to it.

Use these tools as needed, then produce a final answer that is ONLY a YAML
workflow: a `workflow_id` field and a `steps` list, where each step has an
`id`, an `op`, optional `params`, and optional `output`. No explanation,
no markdown fences -- your final message must contain the YAML alone."""


def _extract_text(content) -> str:
    """Normalises a LangChain message's content (str or content-block list) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content) if content else ""


class LangChainAgentBaseline:
    """
    Generates workflows with a LangChain ReAct-style agent -- no WorkflowSynth
    DSL constraints, no formal verification (type checking or taint analysis).
    The agent has tool access for vocabulary lookup and YAML self-checking,
    but nothing enforces that it uses them. Single attempt only. Tests the
    raw output directly against the task's pytest suite, same as
    PureLLMBaseline.
    """

    def __init__(self, dataset_path: str, results_dir: str):
        self.dataset_path = Path(dataset_path)
        self.results_dir = Path(results_dir)
        self.condition = "langchain_agent_baseline"
        self.index = EvaluationRunner._load_index(self.dataset_path / "index.yaml")

        self._out_dir = self.results_dir / self.condition
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def make_tools(self) -> list:
        """Builds the three agent tools, bound to this instance's dataset_path."""
        dataset_path = self.dataset_path

        @tool
        def search_primitives(query: str) -> str:
            """Search the 25 valid WorkflowSynth DSL operators for ones matching
            a keyword (e.g. "database", "notify", "auth"). Returns a
            comma-separated list of matching operator names."""
            query_lower = query.lower().strip()
            ops = sorted(VALID_OPS)
            matches = [op for op in ops if query_lower in op.lower()] if query_lower else ops
            if not matches:
                matches = ops
            return ", ".join(matches)

        @tool
        def validate_yaml(yaml_str: str) -> str:
            """Validate a YAML workflow string. Returns 'valid' if it parses
            correctly (has workflow_id and a well-formed steps list), or a
            description of the parse errors otherwise. Does not check types
            or security rules -- syntax only."""
            result = parse_workflow(yaml_str)
            if result["ok"]:
                return "valid"
            return "; ".join(result["errors"])

        @tool
        def read_spec(task_id: str) -> str:
            """Read the natural language specification (spec.md) for the
            given task_id."""
            spec_path = dataset_path / task_id / "spec.md"
            if not spec_path.exists():
                return f"No spec found for task_id '{task_id}'."
            return spec_path.read_text()

        return [search_primitives, validate_yaml, read_spec]

    def run_agent(self, task_id: str, spec_text: str) -> str:
        """Runs the agent once and returns its final answer's raw text."""
        llm = get_llm(0)  # same model as WorkflowSynth -- claude-opus-4-6
        agent = create_agent(model=llm, tools=self.make_tools(), system_prompt=_AGENT_SYSTEM_PROMPT)
        result = agent.invoke({
            "messages": [HumanMessage(content=f"task_id: {task_id}\n\n{spec_text}")]
        })
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage):
                text = _extract_text(message.content)
                if text.strip():
                    return text.strip()
        return ""

    def run_single(self, task_id: str, spec_text: str = None) -> TaskResult:
        start = time.monotonic()
        meta = self.index.get(task_id, {})

        if spec_text is None:
            spec_text = (self.dataset_path / task_id / "spec.md").read_text()
        test_file = self.dataset_path / task_id / "tests" / f"test_{task_id}.py"

        try:
            raw_output = self.run_agent(task_id, spec_text)
        except Exception as exc:
            record = {
                "attempt_number": 0,
                "llm_sketch": "",
                "dsl_type_errors": [str(exc)],
                "dsl_taint_violations": [],
                "test_results": {},
                "failure_category": "agent_error",
                "success": False,
            }
        else:
            parse_result = parse_workflow(raw_output)

            if not parse_result["ok"]:
                record = {
                    "attempt_number": 0,
                    "llm_sketch": raw_output,
                    "dsl_type_errors": parse_result["errors"],
                    "dsl_taint_violations": [],
                    "test_results": {},
                    "failure_category": "agent_error",
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
