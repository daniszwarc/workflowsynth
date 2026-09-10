#!/usr/bin/env python3
# scripts/synthesize.py
#
# Standalone CLI: runs the WorkflowSynth pipeline on a single spec.md file
# and writes n8n JSON + evidence report output.
#
# Usage:
#   python scripts/synthesize.py examples/invoice_processing.md --out ./output
#   python scripts/synthesize.py spec.md --out ./output --condition no_taint

import argparse
import json
import sys
from pathlib import Path

from langgraph.graph import StateGraph, END

from workflowsynth.synthesis.pipeline import build_pipeline
from workflowsynth.synthesis.state import initial_state
from workflowsynth.synthesis.nodes import (
    translate_to_dsl,
    run_tests,
    check_pass_or_repair,
    repair_with_llm,
    translate_output,
    verify_output,
    record_failure,
)
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.dsl.type_checker import type_check
from workflowsynth.verification.taint import taint_analysis

VALID_CONDITIONS = ("full", "no_taint", "no_verify", "no_repair")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the WorkflowSynth pipeline on a single spec.md file."
    )
    parser.add_argument("spec_file", help="Path to a spec.md file.")
    parser.add_argument(
        "--out", default="./output", help="Directory to write outputs (default: ./output)."
    )
    parser.add_argument(
        "--condition",
        default="full",
        choices=VALID_CONDITIONS,
        help="Ablation condition to run (default: full).",
    )
    return parser.parse_args()


# --- Condition-aware verify_dsl -----------------------------------------------
#
# build_pipeline() in pipeline.py always runs full verification (type check +
# taint analysis) -- it has no notion of ablation conditions. The evaluation
# runner (src/evaluation/runner.py) implements condition-specific verification
# separately from the pipeline, since the pipeline is the "full" production
# path. To support --condition here without modifying pipeline.py/nodes.py,
# this mirrors runner.py's _verify() filtering (no_verify: skip both,
# no_taint: type check only) inside a drop-in replacement for nodes.verify_dsl.

def make_verify_dsl(condition: str):
    def verify_dsl(state):
        yaml_string = state["llm_sketch"]
        parse_result = parse_workflow(yaml_string)

        if not parse_result["ok"]:
            return {
                "dsl_candidate": {},
                "dsl_verification_passed": False,
                "dsl_type_errors": parse_result["errors"],
                "dsl_taint_violations": [],
            }

        ast = parse_result["ast"]

        if condition == "no_verify":
            type_errors, taint_violation_messages = [], []
        elif condition == "no_taint":
            type_errors = type_check(ast)
            taint_violation_messages = []
        else:
            type_errors = type_check(ast)
            taint_violation_messages = [v.message for v in taint_analysis(ast)]

        dsl_candidate = {
            "workflow_id": ast.workflow_id,
            "steps": [
                {"id": s.id, "op": s.op, "params": s.params, "output": s.output}
                for s in ast.steps
            ],
        }

        passed = not type_errors and not taint_violation_messages

        return {
            "dsl_candidate": dsl_candidate,
            "dsl_verification_passed": passed,
            "dsl_type_errors": type_errors,
            "dsl_taint_violations": taint_violation_messages,
        }

    return verify_dsl


def build_condition_pipeline(condition: str):
    """
    Same graph shape as pipeline.build_pipeline(), but with verify_dsl
    swapped for a condition-aware version. Used for every condition
    (including "full", where it behaves identically to build_pipeline()).
    """
    graph = StateGraph(dict)

    graph.add_node("translate_to_dsl", translate_to_dsl)
    graph.add_node("verify_dsl", make_verify_dsl(condition))
    graph.add_node("run_tests", run_tests)
    graph.add_node("translate_output", translate_output)
    graph.add_node("verify_output", verify_output)
    graph.add_node("repair_with_llm", repair_with_llm)
    graph.add_node("record_failure", record_failure)

    graph.set_entry_point("translate_to_dsl")
    graph.add_edge("translate_to_dsl", "verify_dsl")
    graph.add_edge("verify_dsl", "run_tests")
    graph.add_edge("translate_output", "verify_output")
    graph.add_edge("verify_output", END)
    graph.add_edge("record_failure", END)
    graph.add_edge("repair_with_llm", "verify_dsl")

    graph.add_conditional_edges(
        "run_tests",
        check_pass_or_repair,
        {
            "pass": "translate_output",
            "repair": "repair_with_llm",
            "record_failure": "record_failure",
        },
    )

    return graph.compile()


def _classify(state: dict) -> str:
    if state["dsl_type_errors"] and any("YAML" in e for e in state["dsl_type_errors"]):
        return "parse_error"
    if state["dsl_type_errors"]:
        return "type_error"
    if state["dsl_taint_violations"]:
        return "taint_violation"
    if state["test_results"] and not all(state["test_results"].values()):
        return "test_failure"
    return "max_attempts_exceeded"


def _progress_line(attempt_num: int, max_attempts: int, state: dict) -> str:
    verification_passed = state["dsl_verification_passed"]
    tests_passed = all(state["test_results"].values()) if state["test_results"] else False

    if verification_passed and tests_passed:
        return f"Attempt {attempt_num}/{max_attempts}... PASS"

    category = _classify(state)
    if category == "type_error":
        n = len(state["dsl_type_errors"])
        detail = f"({n} error{'s' if n != 1 else ''})"
    elif category == "taint_violation":
        n = len(state["dsl_taint_violations"])
        detail = f"({n} violation{'s' if n != 1 else ''})"
    elif category == "test_failure":
        n = sum(1 for v in state["test_results"].values() if not v)
        detail = f"({n} failed test{'s' if n != 1 else ''})"
    elif category == "parse_error":
        detail = "(parse error)"
    else:
        detail = ""

    return f"Attempt {attempt_num}/{max_attempts}... {category}{(' ' + detail) if detail else ''}"


def run(spec_file: str, out_dir: str, condition: str) -> int:
    spec_path = Path(spec_file)
    natural_language_spec = spec_path.read_text()

    # "full" runs the unmodified production pipeline from pipeline.py.
    # Other conditions use the local variant (see build_condition_pipeline),
    # since build_pipeline() itself has no notion of ablation conditions.
    pipeline = build_pipeline() if condition == "full" else build_condition_pipeline(condition)

    state = initial_state(natural_language_spec)
    if condition == "no_repair":
        state["max_attempts"] = 1
    max_attempts = state["max_attempts"]

    full_state = dict(state)
    attempt_num = 1

    try:
        for update in pipeline.stream(state):
            node_name, partial = next(iter(update.items()))
            full_state.update(partial)

            if node_name == "run_tests":
                print(_progress_line(attempt_num, max_attempts, full_state))
            elif node_name == "repair_with_llm":
                attempt_num += 1
    except Exception as exc:
        print(f"\n✗ Synthesis failed after {attempt_num} attempt{'s' if attempt_num != 1 else ''}")
        print(f"Last error: api_error -- {exc}")
        return 1

    out_path = Path(out_dir)

    if full_state.get("synthesis_successful"):
        out_path.mkdir(parents=True, exist_ok=True)
        n8n_json = full_state["final_n8n_json"]

        evidence_report = {"evidence_report": n8n_json.get("evidence_report", {})}
        workflow_json = {k: v for k, v in n8n_json.items() if k != "evidence_report"}

        workflow_path = out_path / "workflow.json"
        evidence_path = out_path / "evidence_report.json"
        workflow_path.write_text(json.dumps(workflow_json, indent=2))
        evidence_path.write_text(json.dumps(evidence_report, indent=2))

        attempts_used = full_state["repair_attempt"] + 1
        print(f"\n✓ Synthesis successful in {attempts_used} attempt{'s' if attempts_used != 1 else ''}")
        print(f"Output: {workflow_path}")
        print(f"Evidence report: {evidence_path}")
        return 0

    attempts_used = max_attempts
    last_attempt = full_state["attempt_history"][-1] if full_state["attempt_history"] else {}
    category = full_state.get("failure_category", "unknown")
    reason = full_state.get("failure_reason", "")
    error_detail = (
        last_attempt.get("dsl_type_errors")
        or last_attempt.get("dsl_taint_violations")
        or [reason]
    )
    print(f"\n✗ Synthesis failed after {attempts_used} attempt{'s' if attempts_used != 1 else ''}")
    print(f"Last error: {category} -- {error_detail[0] if error_detail else reason}")
    return 1


def main() -> None:
    args = parse_args()
    exit_code = run(args.spec_file, args.out, args.condition)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
