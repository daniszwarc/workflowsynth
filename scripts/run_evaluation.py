#!/usr/bin/env python3
"""CLI entry point for running a WorkflowSynth evaluation experiment.

Usage:
    python scripts/run_evaluation.py \\
        --condition full \\
        --dataset datasets/dataset_a \\
        --results results/ \\
        --tasks wf_pb_001 wf_mm_008   # optional: run subset
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from workflowsynth.evaluation.baselines import LangChainAgentBaseline, PureLLMBaseline
from workflowsynth.evaluation.metrics import (
    by_complexity,
    by_domain,
    mean_attempts,
    pass_at_k,
    security_pass_rate,
    summary_table,
)
from workflowsynth.evaluation.runner import (
    VALID_CONDITIONS,
    EvaluationRunner,
    EvaluationSummary,
    _estimate_cost_usd,
    check_budget_and_warn,
)

BASELINE_CONDITIONS = ("baseline_pure_llm", "baseline_langchain")
ALL_CONDITIONS = VALID_CONDITIONS + BASELINE_CONDITIONS

_BASELINE_CLASSES = {
    "baseline_pure_llm": PureLLMBaseline,
    "baseline_langchain": LangChainAgentBaseline,
}


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments for the evaluation run (condition, dataset, results dir, etc.)."""
    parser = argparse.ArgumentParser(description="Run a WorkflowSynth evaluation experiment.")
    parser.add_argument(
        "--condition",
        required=True,
        choices=ALL_CONDITIONS,
        help="Ablation condition or baseline to run.",
    )
    parser.add_argument(
        "--dataset", required=True, help="Path to the dataset (e.g. datasets/dataset_a)."
    )
    parser.add_argument("--results", required=True, help="Directory to write results into.")
    parser.add_argument(
        "--tasks",
        nargs="*",
        default=None,
        help="Optional subset of task IDs to run. Defaults to the full dataset.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Number of tasks to run concurrently.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Use Batch API for first attempts (50%% cost reduction).",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Warn and prompt when estimated cost reaches 80%% of this USD amount.",
    )
    return parser.parse_args()


def _build_summary(condition: str, results: list) -> EvaluationSummary:
    """Aggregates a list of per-task results into an EvaluationSummary for this condition."""
    total_input_tokens = sum(r.total_input_tokens for r in results)
    total_output_tokens = sum(r.total_output_tokens for r in results)
    return EvaluationSummary(
        condition=condition,
        total_tasks=len(results),
        pass_at_1=pass_at_k(results, 1),
        pass_at_3=pass_at_k(results, 3),
        pass_at_5=pass_at_k(results, 5),
        pass_at_10=pass_at_k(results, 10),
        mean_attempts=mean_attempts(results),
        security_pass_rate=security_pass_rate(results),
        by_complexity=by_complexity(results),
        by_domain=by_domain(results),
        results=results,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        estimated_cost_usd=_estimate_cost_usd(total_input_tokens, total_output_tokens),
    )


def _run_baseline(
    condition: str, dataset: str, results_dir: str, task_ids, budget_limit_usd
) -> EvaluationSummary:
    """
    Runs a baseline (no CLI-level batching or repair loop -- single attempt
    per task) with the same 80%%-of-budget warn-and-prompt behavior as
    EvaluationRunner.
    """
    baseline = _BASELINE_CLASSES[condition](
        dataset_path=dataset, results_dir=results_dir, condition=condition
    )
    ids = task_ids or list(baseline.index.keys())

    results = []
    spent_usd = 0.0
    warning_shown = False

    for task_id in ids:
        result = baseline.run_single(task_id)
        results.append(result)
        spent_usd += _estimate_cost_usd(result.total_input_tokens, result.total_output_tokens)

        warning_shown, stop_requested = check_budget_and_warn(
            spent_usd=spent_usd,
            budget_limit_usd=budget_limit_usd,
            tasks_done=len(results),
            tasks_total=len(ids),
            already_shown=warning_shown,
        )
        if stop_requested:
            break

    return _build_summary(condition, results)


def main() -> None:
    """CLI entry point: dispatches to a baseline or the EvaluationRunner and prints the summary."""
    args = parse_args()

    if args.condition in BASELINE_CONDITIONS:
        summary = _run_baseline(
            condition=args.condition,
            dataset=args.dataset,
            results_dir=args.results,
            task_ids=args.tasks,
            budget_limit_usd=args.budget,
        )
    else:
        runner = EvaluationRunner(
            dataset_path=args.dataset,
            results_dir=args.results,
            condition=args.condition,
            budget_limit_usd=args.budget,
        )

        if args.batch:
            summary = runner.run_dataset_batch(task_ids=args.tasks or None)
        else:
            summary = runner.run_dataset(max_workers=args.max_workers, task_ids=args.tasks)

    print(summary_table(summary.results))

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    summary_path = Path(args.results) / f"summary_{args.condition}_{timestamp}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(asdict(summary), indent=2))

    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()
