"""Statistical analysis of Session 09 results for the dissertation.

Reads per-task JSON result files from results/session_09/<condition>/*.json
and produces the main results table, ablation/baseline comparisons,
complexity/domain/failure-taxonomy breakdowns, paired statistical tests,
and a token/cost summary. Prints plain-text tables to stdout and writes
results/session_09/analysis_summary.json.
"""

from __future__ import annotations

import glob
import json
import math
import statistics
from pathlib import Path

from scipy import stats

RESULTS_DIR = Path("results/session_09")
CONDITIONS = [
    "full",
    "no_repair",
    "no_verify",
    "no_taint",
    "baseline_pure_llm",
    "baseline_langchain",
]
BASELINE_CONDITION = "full"
K_VALUES = [1, 3, 5, 10]
INPUT_PRICE_PER_M = 5.0   # USD per 1M input tokens (matches run_full_experiment.sh check_spend)
OUTPUT_PRICE_PER_M = 25.0  # USD per 1M output tokens
ALPHA = 0.05

# baseline_langchain contains tasks that never reached the LLM due to an
# Anthropic billing failure ("credit balance is too low") -- these are
# infrastructure failures, not synthesis attempts, and are excluded.
INFRA_ERROR_SIGNATURE = "credit balance is too low"


def is_infra_failure(record: dict) -> bool:
    if record.get("failure_category") != "agent_error":
        return False
    for attempt in record.get("attempt_history", []):
        for err in attempt.get("dsl_type_errors", []):
            if INFRA_ERROR_SIGNATURE in err:
                return True
    return False


def load_condition(condition: str) -> list[dict]:
    files = sorted(glob.glob(str(RESULTS_DIR / condition / "*.json")))
    records = []
    for f in files:
        with open(f) as fh:
            record = json.load(fh)
        if is_infra_failure(record):
            continue
        records.append(record)
    return records


def pass_at_k(records: list[dict], k: int) -> float:
    if not records:
        return 0.0
    hits = sum(1 for r in records if r.get("pass_at_k", {}).get(str(k), False))
    return hits / len(records)


def mean_attempts_successful(records: list[dict]) -> float:
    successes = [r["attempts_used"] for r in records if r.get("success")]
    return statistics.mean(successes) if successes else 0.0


def security_pass_at_10(records: list[dict]) -> tuple[float, int]:
    sec = [r for r in records if r.get("has_security_constraint")]
    if not sec:
        return 0.0, 0
    return pass_at_k(sec, 10), len(sec)


def cohens_d_paired(a: list[float], b: list[float]) -> float:
    diffs = [x - y for x, y in zip(a, b)]
    if len(diffs) < 2:
        return 0.0
    sd = statistics.stdev(diffs)
    if sd == 0:
        return 0.0
    return statistics.mean(diffs) / sd


def wilson_or_normal_ci_diff(p1: float, n1: int, p2: float, n2: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Normal-approximation 95% CI on the difference of two proportions (paired-friendly enough
    for reporting pass@10 deltas; n1 == n2 in all comparisons here since tasks are the same set)."""
    z = stats.norm.ppf(1 - alpha / 2)
    se = math.sqrt((p1 * (1 - p1)) / n1 + (p2 * (1 - p2)) / n2) if n1 and n2 else 0.0
    diff = p1 - p2
    return diff - z * se, diff + z * se


def build_task_map(records: list[dict]) -> dict[str, dict]:
    return {r["task_id"]: r for r in records}


def paired_success_vectors(full_map: dict[str, dict], other_map: dict[str, dict]) -> tuple[list[int], list[int]]:
    common_ids = [tid for tid in full_map if tid in other_map]
    full_vec = [1 if full_map[tid].get("success") else 0 for tid in common_ids]
    other_vec = [1 if other_map[tid].get("success") else 0 for tid in common_ids]
    return full_vec, other_vec


def token_cost(records: list[dict]) -> tuple[int, int, float]:
    total_in = sum(r.get("total_input_tokens", 0) for r in records)
    total_out = sum(r.get("total_output_tokens", 0) for r in records)
    cost = total_in / 1e6 * INPUT_PRICE_PER_M + total_out / 1e6 * OUTPUT_PRICE_PER_M
    return total_in, total_out, cost


def fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def fmt_pp(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}{x * 100:.2f}pp"


def main() -> None:
    data = {c: load_condition(c) for c in CONDITIONS}
    task_maps = {c: build_task_map(recs) for c, recs in data.items()}

    lines: list[str] = []

    def p(s: str = "") -> None:
        lines.append(s)
        print(s)

    p("=" * 100)
    p("SESSION 09 -- STATISTICAL ANALYSIS (Dataset A)")
    p("=" * 100)
    p()
    for c in CONDITIONS:
        note = " (PARTIAL -- infra failures excluded, see below)" if c == "baseline_langchain" else ""
        p(f"  {c}: {len(data[c])} valid tasks{note}")
    if "baseline_langchain" in data:
        raw_count = len(glob.glob(str(RESULTS_DIR / "baseline_langchain" / "*.json")))
        excluded = raw_count - len(data["baseline_langchain"])
        p(f"    -> baseline_langchain: {raw_count} files on disk, {excluded} excluded "
          f"(Anthropic API billing failure: '{INFRA_ERROR_SIGNATURE}'), {len(data['baseline_langchain'])} valid")
    p()

    # ------------------------------------------------------------------
    # 1. MAIN RESULTS TABLE
    # ------------------------------------------------------------------
    p("-" * 100)
    p("1. MAIN RESULTS TABLE")
    p("-" * 100)
    header = f"{'condition':<22}{'n':>5}{'pass@1':>10}{'pass@3':>10}{'pass@5':>10}{'pass@10':>10}{'mean_attempts':>16}{'sec_pass@10':>14}{'n_sec':>7}"
    p(header)
    p("-" * len(header))

    main_results = {}
    for c in CONDITIONS:
        recs = data[c]
        pk = {k: pass_at_k(recs, k) for k in K_VALUES}
        ma = mean_attempts_successful(recs)
        sp10, n_sec = security_pass_at_10(recs)
        main_results[c] = {
            "n_tasks": len(recs),
            "pass_at_1": pk[1],
            "pass_at_3": pk[3],
            "pass_at_5": pk[5],
            "pass_at_10": pk[10],
            "mean_attempts_successful": ma,
            "security_pass_at_10": sp10,
            "n_security_tasks": n_sec,
        }
        p(f"{c:<22}{len(recs):>5}{fmt_pct(pk[1]):>10}{fmt_pct(pk[3]):>10}{fmt_pct(pk[5]):>10}"
          f"{fmt_pct(pk[10]):>10}{ma:>16.2f}{fmt_pct(sp10):>14}{n_sec:>7}")
    p()

    # ------------------------------------------------------------------
    # 2. ABLATION COMPARISON
    # ------------------------------------------------------------------
    p("-" * 100)
    p("2. ABLATION COMPARISON (baseline = full)")
    p("-" * 100)
    ablation = {}
    ablation_notes = {
        "no_repair": "Removing the repair loop -- shows how much the iterative repair mechanism contributes to pass@10.",
        "no_verify": "Removing verification -- shows how much verification-gated retries contribute to pass@10.",
        "no_taint": "Removing taint tracking -- shows how much taint analysis contributes to pass@10.",
    }
    full_pass10 = main_results["full"]["pass_at_10"]
    for c in ["no_repair", "no_verify", "no_taint"]:
        delta = main_results[c]["pass_at_10"] - full_pass10
        ablation[c] = {"pass_at_10": main_results[c]["pass_at_10"], "delta_vs_full_pp": delta * 100}
        p(f"  {c:<15} pass@10={fmt_pct(main_results[c]['pass_at_10']):>8}  delta vs full: {fmt_pp(delta):>10}")
        p(f"    -> {ablation_notes[c]}")
    p()

    # ------------------------------------------------------------------
    # 3. BASELINE COMPARISON
    # ------------------------------------------------------------------
    p("-" * 100)
    p("3. BASELINE COMPARISON (baseline = full)")
    p("-" * 100)
    baseline_comp = {}
    baseline_notes = {
        "baseline_pure_llm": "Pure LLM synthesis with no DSL scaffolding -- shows the gap closed by the full WorkflowSynth pipeline.",
        "baseline_langchain": "LangChain agent baseline (PARTIAL, 37/60 valid tasks) -- shows the gap closed vs. an off-the-shelf agent framework.",
    }
    for c in ["baseline_pure_llm", "baseline_langchain"]:
        delta = main_results[c]["pass_at_10"] - full_pass10
        baseline_comp[c] = {
            "pass_at_10": main_results[c]["pass_at_10"],
            "delta_vs_full_pp": delta * 100,
            "n_tasks": main_results[c]["n_tasks"],
            "partial": c == "baseline_langchain",
        }
        partial_tag = f" [PARTIAL: {main_results[c]['n_tasks']}/60 valid]" if c == "baseline_langchain" else ""
        p(f"  {c:<20} pass@10={fmt_pct(main_results[c]['pass_at_10']):>8}  delta vs full: {fmt_pp(delta):>10}{partial_tag}")
        p(f"    -> {baseline_notes[c]}")
    p()

    # ------------------------------------------------------------------
    # 4. BY COMPLEXITY (full only)
    # ------------------------------------------------------------------
    p("-" * 100)
    p("4. BY COMPLEXITY (condition=full)")
    p("-" * 100)
    by_complexity = {}
    full_recs = data["full"]
    for complexity in sorted({r["complexity"] for r in full_recs}):
        subset = [r for r in full_recs if r["complexity"] == complexity]
        pk10 = pass_at_k(subset, 10)
        by_complexity[str(complexity)] = {"pass_at_10": pk10, "n_tasks": len(subset)}
        p(f"  complexity {complexity}: pass@10={fmt_pct(pk10):>8}  (n={len(subset)})")
    p()

    # ------------------------------------------------------------------
    # 5. BY DOMAIN (full only)
    # ------------------------------------------------------------------
    p("-" * 100)
    p("5. BY DOMAIN (condition=full, sorted descending by pass@10)")
    p("-" * 100)
    by_domain = {}
    for domain in {r["domain"] for r in full_recs}:
        subset = [r for r in full_recs if r["domain"] == domain]
        pk10 = pass_at_k(subset, 10)
        by_domain[domain] = {"pass_at_10": pk10, "n_tasks": len(subset)}
    for domain, v in sorted(by_domain.items(), key=lambda kv: kv[1]["pass_at_10"], reverse=True):
        p(f"  {domain:<25} pass@10={fmt_pct(v['pass_at_10']):>8}  (n={v['n_tasks']})")
    p()

    # ------------------------------------------------------------------
    # 6. FAILURE TAXONOMY (full only)
    # ------------------------------------------------------------------
    p("-" * 100)
    p("6. FAILURE TAXONOMY (condition=full, from attempt_history)")
    p("-" * 100)
    per_attempt_counts: dict[int, dict[str, int]] = {}
    for r in full_recs:
        for attempt in r.get("attempt_history", []):
            n = attempt.get("attempt_number", 0) + 1  # 1-indexed for readability
            bucket = n if n <= 3 else 3  # attempt 3+ collapsed
            fc = attempt.get("failure_category", "unknown")
            per_attempt_counts.setdefault(bucket, {})
            per_attempt_counts[bucket][fc] = per_attempt_counts[bucket].get(fc, 0) + 1

    failure_taxonomy = {}
    for bucket in sorted(per_attempt_counts):
        label = f"attempt {bucket}" if bucket < 3 else "attempt 3+"
        counts = per_attempt_counts[bucket]
        total = sum(counts.values())
        most_common = max(counts.items(), key=lambda kv: kv[1])
        failure_taxonomy[label] = counts
        p(f"  {label} (n={total}):")
        for fc, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            p(f"      {fc:<20} {cnt:>4}")
        p(f"    -> most common: {most_common[0]} ({most_common[1]})")

    avg_attempts_success = mean_attempts_successful(full_recs)
    failed_recs = [r for r in full_recs if not r.get("success")]
    avg_attempts_failed = statistics.mean([r["attempts_used"] for r in failed_recs]) if failed_recs else 0.0
    p()
    p(f"  Average attempts before success (successful tasks): {avg_attempts_success:.2f}")
    p(f"  Average attempts for failed tasks:                  {avg_attempts_failed:.2f}")
    failure_taxonomy_summary = {
        "per_attempt_bucket": failure_taxonomy,
        "avg_attempts_before_success": avg_attempts_success,
        "avg_attempts_failed_tasks": avg_attempts_failed,
    }
    p()

    # ------------------------------------------------------------------
    # 7. STATISTICAL TESTS
    # ------------------------------------------------------------------
    p("-" * 100)
    p("7. STATISTICAL TESTS (paired, vs. full; alpha=0.05)")
    p("-" * 100)
    stat_tests = {}
    full_map = task_maps["full"]
    for c in [x for x in CONDITIONS if x != "full"]:
        other_map = task_maps[c]
        full_vec, other_vec = paired_success_vectors(full_map, other_map)
        n = len(full_vec)
        if n < 2 or len(set(full_vec + other_vec)) < 2:
            p(f"  full vs {c}: insufficient variance/n={n} for paired t-test -- skipped")
            stat_tests[c] = {"n": n, "note": "insufficient variance or n<2, test skipped"}
            p()
            continue

        t_stat, p_val = stats.ttest_rel(full_vec, other_vec)
        d = cohens_d_paired(full_vec, other_vec)
        p1 = sum(full_vec) / n
        p2 = sum(other_vec) / n
        ci_lo, ci_hi = wilson_or_normal_ci_diff(p1, n, p2, n)
        significant = p_val < ALPHA

        stat_tests[c] = {
            "n": n,
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "cohens_d": float(d),
            "pass_at_10_diff": float(p1 - p2),
            "ci_95_low": float(ci_lo),
            "ci_95_high": float(ci_hi),
            "significant": bool(significant),
        }
        p(f"  full vs {c} (n={n}):")
        p(f"    t={t_stat:.4f}  p={p_val:.6f}  Cohen's d={d:.4f}")
        p(f"    pass@10 diff={fmt_pp(p1 - p2)}  95% CI=[{ci_lo * 100:.2f}pp, {ci_hi * 100:.2f}pp]")
        p(f"    significant at alpha={ALPHA}: {'Yes' if significant else 'No'}")
        p()

    # ------------------------------------------------------------------
    # 8. COST SUMMARY
    # ------------------------------------------------------------------
    p("-" * 100)
    p("8. COST SUMMARY")
    p("-" * 100)
    cost_summary = {}
    grand_in, grand_out, grand_cost = 0, 0, 0.0
    for c in CONDITIONS:
        total_in, total_out, cost = token_cost(data[c])
        if c == "baseline_langchain":
            cost = 0.0  # known token tracking gap for this condition
        cost_summary[c] = {"input_tokens": total_in, "output_tokens": total_out, "cost_usd": cost}
        grand_in += total_in
        grand_out += total_out
        grand_cost += cost
        note = "  (known token tracking gap -- cost not billed/tracked)" if c == "baseline_langchain" else ""
        p(f"  {c:<22} in={total_in:>10,}  out={total_out:>10,}  cost=${cost:>8.4f}{note}")
    p("-" * 100)
    p(f"  {'GRAND TOTAL (tracked)':<22} in={grand_in:>10,}  out={grand_out:>10,}  cost=${grand_cost:>8.4f}")
    cost_summary["grand_total"] = {"input_tokens": grand_in, "output_tokens": grand_out, "cost_usd": grand_cost}
    p()

    # ------------------------------------------------------------------
    # Save JSON
    # ------------------------------------------------------------------
    summary = {
        "main_results": main_results,
        "ablation_comparison": ablation,
        "baseline_comparison": baseline_comp,
        "by_complexity": by_complexity,
        "by_domain": by_domain,
        "failure_taxonomy": failure_taxonomy_summary,
        "statistical_tests": stat_tests,
        "cost_summary": cost_summary,
        "notes": {
            "baseline_langchain": f"37/60 valid tasks; {23} excluded due to Anthropic API billing "
                                   f"failure ('{INFRA_ERROR_SIGNATURE}'), not real synthesis attempts.",
        },
    }
    out_path = RESULTS_DIR / "analysis_summary.json"
    with open(out_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    p(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
