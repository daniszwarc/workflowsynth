# src/evaluation/metrics.py
#
# Metric functions computed over a list of TaskResult objects.
# All metrics operate on the already-completed results -- no I/O here.


def pass_at_k(results: list, k: int) -> float:
    """
    Fraction of tasks where success occurred within k attempts.

    A task counts as passing@k if it succeeded and did so using at most
    k attempts (attempts_used <= k). This holds even when the run's
    max_attempts was itself less than k (e.g. a "no_repair" run that
    succeeded on attempt 1 counts towards pass@10 too).
    """
    if not results:
        return 0.0

    passed = sum(1 for r in results if r.success and r.attempts_used <= k)
    return passed / len(results)


def mean_attempts(results: list) -> float:
    """Mean attempts_used across successful tasks only. 0.0 if none succeeded."""
    successful = [r.attempts_used for r in results if r.success]
    if not successful:
        return 0.0
    return sum(successful) / len(successful)


def security_pass_rate(results: list) -> float:
    """pass@10 rate restricted to tasks with has_security_constraint = True."""
    security_results = [r for r in results if r.has_security_constraint]
    return pass_at_k(security_results, 10)


def by_complexity(results: list) -> dict:
    """pass@10 rate broken down by complexity level."""
    levels = sorted({r.complexity for r in results})
    return {
        level: pass_at_k([r for r in results if r.complexity == level], 10)
        for level in levels
    }


def by_domain(results: list) -> dict:
    """pass@10 rate broken down by domain."""
    domains = sorted({r.domain for r in results})
    return {
        domain: pass_at_k([r for r in results if r.domain == domain], 10)
        for domain in domains
    }


def summary_table(results: list) -> str:
    """Formatted text table of all metrics, for printing/logging."""
    if not results:
        return "No results to summarise."

    condition = results[0].condition
    lines = [
        f"Evaluation summary -- condition: {condition}",
        f"Total tasks: {len(results)}",
        "",
        f"{'Metric':<24}{'Value':>10}",
        "-" * 34,
        f"{'pass@1':<24}{pass_at_k(results, 1):>10.2%}",
        f"{'pass@3':<24}{pass_at_k(results, 3):>10.2%}",
        f"{'pass@5':<24}{pass_at_k(results, 5):>10.2%}",
        f"{'pass@10':<24}{pass_at_k(results, 10):>10.2%}",
        f"{'mean attempts (success)':<24}{mean_attempts(results):>10.2f}",
        f"{'security pass@10':<24}{security_pass_rate(results):>10.2%}",
        "",
        "By complexity (pass@10):",
    ]
    for level, rate in by_complexity(results).items():
        lines.append(f"  complexity {level:<12}{rate:>10.2%}")

    lines.append("")
    lines.append("By domain (pass@10):")
    for domain, rate in by_domain(results).items():
        lines.append(f"  {domain:<22}{rate:>10.2%}")

    return "\n".join(lines)
