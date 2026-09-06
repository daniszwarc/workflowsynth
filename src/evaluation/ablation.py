# src/evaluation/ablation.py
#
# Thin wrapper around EvaluationRunner that makes ablation runs explicit
# in experiment scripts, rather than constructing EvaluationRunner directly
# with a condition string.

from .runner import EvaluationRunner, EvaluationSummary, VALID_CONDITIONS


def run_ablation(
    condition: str,
    dataset_path: str,
    results_dir: str,
    task_ids: list = None,
) -> EvaluationSummary:
    """
    Runs the given ablation condition against Dataset A (or a subset).

    condition: one of "full", "no_taint", "no_repair", "no_verify".
    """
    if condition not in VALID_CONDITIONS:
        raise ValueError(f"Unknown ablation condition {condition!r}. Must be one of {VALID_CONDITIONS}.")

    runner = EvaluationRunner(dataset_path, results_dir, condition=condition)
    return runner.run_dataset(task_ids=task_ids)
