#!/usr/bin/env python3
# scripts/run_evaluation.py
#
# CLI entry point for running a WorkflowSynth evaluation experiment.
#
# Usage:
#   python scripts/run_evaluation.py \
#       --condition full \
#       --dataset datasets/dataset_a \
#       --results results/ \
#       --tasks wf_pb_001 wf_mm_008   # optional: run subset

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from workflowsynth.evaluation.runner import EvaluationRunner, VALID_CONDITIONS, EvaluationSummary, _estimate_cost_usd
from workflowsynth.evaluation.baselines import PureLLMBaseline, LangChainAgentBaseline
from workflowsynth.evaluation.metrics import (
    summary_table,
    pass_at_k,
    mean_attempts,
    security_pass_rate,
    by_complexity,
    by_domain,
)

BASELINE_CONDITIONS = ("baseline_pure_llm", "baseline_langchain")
ALL_CONDITIONS = VALID_CONDITIONS + BASELINE_CONDITIONS

_BASELINE_CLASSES = {
    "baseline_pure_llm": PureLLMBaseline,
    "baseline_langchain": LangChainAgentBaseline,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a WorkflowSynth evaluation experiment.")
    parser.add_argument(
        "--condition",
        required=True,
        choices=ALL_CONDITIONS,
        help="Ablation condition or baseline to run.",
    )
    parser.add_argument("--dataset", required=True, help="Path to the dataset (e.g. datasets/dataset_a).")
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


def _run_baseline(condition: str, dataset: str, results_dir: str, task_ids, budget_limit_usd) -> EvaluationSummary:
    """
    Runs a baseline (no CLI-level batching or repair loop -- single attempt
    per task) with the same 80%%-of-budget warn-and-prompt behavior as
    EvaluationRunner.
    """
    baseline = _BASELINE_CLASSES[condition](dataset_path=dataset, results_dir=results_dir, condition=condition)
    ids = task_ids or list(baseline.index.keys())

    results = []
    spent_usd = 0.0
    warning_shown = False

    for task_id in ids:
        result = baseline.run_single(task_id)
        results.append(result)
        spent_usd += _estimate_cost_usd(result.total_input_tokens, result.total_output_tokens)

        if budget_limit_usd and spent_usd >= budget_limit_usd * 0.80 and not warning_shown:
            warning_shown = True
            pct = len(results) / len(ids) * 100
            print(
                f"\n*** BUDGET WARNING ***\n"
                f"Spent so far: ${spent_usd:.2f} USD\n"
                f"Budget limit: ${budget_limit_usd:.2f} USD (80% reached)\n"
                f"Progress: {len(results)}/{len(ids)} tasks ({pct:.1f}%)\n"
                f"Continue? [Y/n]: ",
                file=sys.stderr, end="", flush=True,
            )
            answer = input().strip().lower()
            if answer == "n":
                print("Stopping experiment. Results saved so far are complete.")
                break
            else:
                print("Continuing...\n")

    return _build_summary(condition, results)


def main() -> None:
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
