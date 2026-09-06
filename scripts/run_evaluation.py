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
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from workflowsynth.evaluation.runner import EvaluationRunner, VALID_CONDITIONS
from workflowsynth.evaluation.metrics import summary_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a WorkflowSynth evaluation experiment.")
    parser.add_argument(
        "--condition",
        required=True,
        choices=VALID_CONDITIONS,
        help="Ablation condition to run.",
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    runner = EvaluationRunner(
        dataset_path=args.dataset,
        results_dir=args.results,
        condition=args.condition,
    )

    summary = runner.run_dataset(max_workers=args.max_workers, task_ids=args.tasks)

    print(summary_table(summary.results))

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    summary_path = Path(args.results) / f"summary_{args.condition}_{timestamp}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(asdict(summary), indent=2))

    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()
