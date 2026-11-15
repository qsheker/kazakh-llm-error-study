#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import fasttext
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kazllm_eval.annotation import EVENT_CATEGORIES, RESPONSE_FLAGS, load_run_records
from kazllm_eval.core import sha256_file
from kazllm_eval.detectors import (
    binary_metrics,
    clustered_f1_difference,
    fasttext_response_positive,
    latin_response_positive,
)
from kazllm_eval.statistics import (
    friedman_permutation,
    holm_adjust,
    pratt_signed_rank_permutation,
    rank_biserial,
    stratified_prompt_bootstrap_difference,
)

PRIMARY_CATEGORIES = EVENT_CATEGORIES[:4]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stratified_model_interval(values: np.ndarray, strata: list[str], replicates: int, seed: int) -> tuple[float, float]:
    strata_array = np.asarray(strata)
    groups = [np.flatnonzero(strata_array == label) for label in np.unique(strata_array)]
    rng = np.random.default_rng(seed)
    estimates = np.empty(replicates)
    for index in range(replicates):
        sampled = np.concatenate([rng.choice(group, size=len(group), replace=True) for group in groups])
        estimates[index] = float(np.mean(values[sampled]))
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the frozen final statistical outputs from adjudicated labels.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/final_test_v2"))
    parser.add_argument("--mapping", type=Path, default=Path("data/blinding/private_model_key.csv"))
    parser.add_argument("--responses", type=Path, default=Path("annotations/adjudicated/response_labels.csv"))
    parser.add_argument("--events", type=Path, default=Path("annotations/adjudicated/error_events.csv"))
    parser.add_argument(
        "--adjudication-log",
        type=Path,
        default=Path("annotations/adjudicated/adjudication_log.csv"),
    )
    parser.add_argument("--exemptions", type=Path, default=Path("config/latin_exemptions.txt"))
    parser.add_argument("--lid-model", type=Path, default=Path("resources/lid.176.ftz"))
    parser.add_argument("--output", type=Path, default=Path("results/derived/final_test_v2"))
    parser.add_argument("--permutations", type=int)
    parser.add_argument("--bootstrap", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    resolve = lambda path: path if path.is_absolute() else root / path
    run_dir = resolve(args.run_dir)
    mapping_path = resolve(args.mapping)
    responses_path = resolve(args.responses)
    events_path = resolve(args.events)
    adjudication_log_path = resolve(args.adjudication_log)
    exemptions_path = resolve(args.exemptions)
    lid_path = resolve(args.lid_model)
    output = resolve(args.output)
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refused: final output directory is not empty: {output}")

    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    permutations = args.permutations or int(protocol["analysis"]["permutations"])
    bootstrap = args.bootstrap or int(protocol["analysis"]["bootstrap_replicates"])
    seed = int(protocol["analysis"]["analysis_seed"])
    model_order = [model["label"] for model in protocol["models"]]
    if len(model_order) != 4:
        raise SystemExit("final analysis requires exactly four frozen model labels")

    records = load_run_records(run_dir)
    if len(records) != 240:
        raise SystemExit(f"expected 240 run records, found {len(records)}")
    by_private = {record["private_response_id"]: record for record in records}
    mapping_rows = read_csv(mapping_path)
    if len(mapping_rows) != 240 or len({row["blind_id"] for row in mapping_rows}) != 240:
        raise SystemExit("private mapping must contain exactly 240 unique blind IDs")
    mapping = {row["blind_id"]: row for row in mapping_rows}
    for row in mapping_rows:
        record = by_private.get(row["private_response_id"])
        if record is None or record["response_sha256"] != row["response_sha256"]:
            raise SystemExit(f"mapping does not match immutable receipt for {row['blind_id']}")

    response_rows = read_csv(responses_path)
    if len(response_rows) != 240 or {row["blind_id"] for row in response_rows} != set(mapping):
        raise SystemExit("adjudicated response file must contain exactly the 240 mapped blind IDs")
    response_labels = {row["blind_id"]: row for row in response_rows}
    for blind_id, row in response_labels.items():
        for flag in RESPONSE_FLAGS:
            if row.get(flag) not in {"yes", "no"}:
                raise SystemExit(f"{blind_id}: final {flag} must be yes or no")

    event_rows = read_csv(events_path)
    event_counts = defaultdict(Counter)
    event_ids = set()
    for row in event_rows:
        blind_id = row.get("blind_id", "")
        category = row.get("category", "")
        if blind_id not in mapping or category not in EVENT_CATEGORIES:
            raise SystemExit(f"invalid final event identity/category: {blind_id}/{category}")
        record = by_private[mapping[blind_id]["private_response_id"]]
        event_key = (blind_id, row.get("event_id", ""))
        if not event_key[1] or event_key in event_ids:
            raise SystemExit(f"missing or duplicate final event ID: {blind_id}/{event_key[1]}")
        event_ids.add(event_key)
        try:
            start = int(row["start_offset_zero_based"])
            end = int(row["end_offset_exclusive"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"{blind_id}: event offsets must be integers") from exc
        if (
            start < 0
            or end <= start
            or end > len(record["response_text"])
            or record["response_text"][start:end] != row.get("exact_fragment", "")
        ):
            raise SystemExit(f"{blind_id}: final event fragment does not match immutable response")
        if not row.get("adjudicator") or not row.get("adjudication_rationale"):
            raise SystemExit(f"{blind_id}: every final event requires adjudicator and rationale")
        event_counts[blind_id][category] += 1

    metrics = []
    for blind_id, map_row in mapping.items():
        record = by_private[map_row["private_response_id"]]
        counts = event_counts[blind_id]
        primary_count = sum(counts[category] for category in PRIMARY_CATEGORIES)
        word_count = int(record["word_count"])
        rate = None if word_count == 0 else 100 * primary_count / word_count
        metrics.append(
            {
                "blind_id": blind_id,
                "private_response_id": record["private_response_id"],
                "prompt_id": record["prompt_id"],
                "task_type": record["task_type"],
                "model_label": record["model_label"],
                "word_count": word_count,
                **{category: counts[category] for category in EVENT_CATEGORIES},
                "primary_count": primary_count,
                "primary_rate_per_100_words": rate,
                **{flag: response_labels[blind_id][flag] for flag in RESPONSE_FLAGS},
            }
        )

    by_prompt: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in metrics:
        by_prompt[row["prompt_id"]][row["model_label"]] = row
    complete_prompts = [
        prompt_id
        for prompt_id, rows in sorted(by_prompt.items())
        if set(rows) == set(model_order) and all(rows[model]["primary_rate_per_100_words"] is not None for model in model_order)
    ]
    matrix = np.array(
        [[by_prompt[prompt_id][model]["primary_rate_per_100_words"] for model in model_order] for prompt_id in complete_prompts],
        dtype=float,
    )
    strata = [by_prompt[prompt_id][model_order[0]]["task_type"] for prompt_id in complete_prompts]
    if len(complete_prompts) < 2:
        raise SystemExit("fewer than two complete four-model prompt blocks remain")

    friedman, kendalls_w = friedman_permutation(matrix, permutations=permutations, seed=seed)
    pairwise = []
    for pair_index, (left_index, right_index) in enumerate(itertools.combinations(range(4), 2)):
        left = matrix[:, left_index]
        right = matrix[:, right_index]
        test = pratt_signed_rank_permutation(
            left, right, permutations=permutations, seed=seed + pair_index + 1
        )
        interval = stratified_prompt_bootstrap_difference(
            matrix,
            strata,
            left_index,
            right_index,
            replicates=bootstrap,
            seed=seed + pair_index + 101,
        )
        pairwise.append(
            {
                "left": model_order[left_index],
                "right": model_order[right_index],
                "statistic": test.statistic,
                "p_raw": test.p_value,
                "rank_biserial": rank_biserial(left, right),
                **interval,
            }
        )
    adjusted = holm_adjust(row["p_raw"] for row in pairwise)
    for row, value in zip(pairwise, adjusted):
        row["p_holm"] = value

    model_rows = []
    for model_index, model in enumerate(model_order):
        model_metrics = [row for row in metrics if row["model_label"] == model]
        defined = np.array(
            [
                row["primary_rate_per_100_words"]
                for row in model_metrics
                if row["primary_rate_per_100_words"] is not None
            ]
        )
        block_values = matrix[:, model_index]
        low, high = stratified_model_interval(block_values, strata, bootstrap, seed + 501 + model_index)
        total_words = sum(row["word_count"] for row in model_metrics)
        total_events = sum(row["primary_count"] for row in model_metrics)
        model_rows.append(
            {
                "model": model,
                "responses": len(model_metrics),
                "defined_responses": len(defined),
                "total_words": total_words,
                "total_primary_events": total_events,
                "pooled_rate_per_100_words": None if total_words == 0 else 100 * total_events / total_words,
                "all_defined_mean_response_rate": float(np.mean(defined)) if len(defined) else None,
                "all_defined_median_response_rate": float(np.median(defined)) if len(defined) else None,
                "mean_complete_block_rate": float(np.mean(block_values)),
                "cluster_ci_low": low,
                "cluster_ci_high": high,
            }
        )

    h2_pair = next(row for row in pairwise if {row["left"], row["right"]} == {"kazllm_8b", "llama31_8b"})
    h2_difference = h2_pair["difference"] if h2_pair["left"] == "kazllm_8b" else -h2_pair["difference"]
    h2_low = h2_pair["ci_low"] if h2_pair["left"] == "kazllm_8b" else -h2_pair["ci_high"]
    h2_high = h2_pair["ci_high"] if h2_pair["left"] == "kazllm_8b" else -h2_pair["ci_low"]
    h1_supported = friedman.p_value < float(protocol["analysis"]["alpha"])
    h2_supported = h1_supported and h2_pair["p_holm"] < 0.05 and h2_difference < 0 and h2_high < 0

    general_models = {"qwen3_8b", "llama31_8b", "gemma3_12b"}
    general_rows = [row for row in metrics if row["model_label"] in general_models]
    general_words = sum(row["word_count"] for row in general_rows)
    h3_rates = {
        category: (100 * sum(row[category] for row in general_rows) / general_words if general_words else None)
        for category in PRIMARY_CATEGORIES
    }
    h3_top = max(h3_rates, key=lambda key: h3_rates[key] if h3_rates[key] is not None else -1)

    exemptions = {
        line.strip().casefold()
        for line in exemptions_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    lid = fasttext.load_model(str(lid_path))

    def predictor(text: str) -> tuple[str, float]:
        labels, probabilities = lid.predict(text.replace("\n", " "), k=1)
        return labels[0].removeprefix("__label__"), float(probabilities[0])

    detector_rows = []
    for row in metrics:
        record = by_private[row["private_response_id"]]
        latin = latin_response_positive(record["response_text"], exemptions)
        fasttext_positive, _ = fasttext_response_positive(
            record["response_text"],
            predictor,
            threshold=float(protocol["analysis"]["language_id_threshold"]),
            exemptions=exemptions,
        )
        detector_rows.append(
            {
                "prompt_id": row["prompt_id"],
                "blind_id": row["blind_id"],
                "gold": row["code_switching"] > 0,
                "latin": latin,
                "fasttext": fasttext_positive,
                "hybrid": latin or fasttext_positive,
            }
        )
    gold = [row["gold"] for row in detector_rows]
    latin_values = [row["latin"] for row in detector_rows]
    hybrid_values = [row["hybrid"] for row in detector_rows]
    h4 = {
        "latin": binary_metrics(latin_values, gold),
        "fasttext": binary_metrics([row["fasttext"] for row in detector_rows], gold),
        "hybrid": binary_metrics(hybrid_values, gold),
        "hybrid_minus_latin": clustered_f1_difference(
            latin_values,
            hybrid_values,
            gold,
            [row["prompt_id"] for row in detector_rows],
            replicates=bootstrap,
            seed=seed,
        ),
    }

    summary = {
        "design": {"responses": len(metrics), "complete_prompt_blocks": len(complete_prompts)},
        "h1": {
            "supported": h1_supported,
            "friedman_statistic": friedman.statistic,
            "p_value": friedman.p_value,
            "permutations": friedman.permutations,
            "kendalls_w": kendalls_w,
        },
        "h2": {
            "supported": h2_supported,
            "kazllm_minus_llama": h2_difference,
            "ci_low": h2_low,
            "ci_high": h2_high,
            "p_holm": h2_pair["p_holm"],
        },
        "h3": {"descriptive_top_category": h3_top, "rates_per_100_words": h3_rates},
        "h4": h4,
        "models": model_rows,
        "pairwise": pairwise,
    }

    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", summary)
    write_json(output / "detector_metrics.json", h4)
    write_csv(
        output / "response_metrics.csv",
        list(metrics[0]),
        metrics,
    )
    write_csv(output / "model_rates.csv", list(model_rows[0]), model_rows)
    write_csv(output / "pairwise.csv", list(pairwise[0]), pairwise)
    write_json(
        output / "input_hashes.json",
        {
            "run_manifest": sha256_file(run_dir / "manifest.json"),
            "private_mapping": sha256_file(mapping_path),
            "response_labels": sha256_file(responses_path),
            "error_events": sha256_file(events_path),
            "adjudication_log": sha256_file(adjudication_log_path),
            "exemptions": sha256_file(exemptions_path),
            "lid_model": sha256_file(lid_path),
        },
    )

    labels = [row["model"] for row in model_rows]
    means = np.array([row["mean_complete_block_rate"] for row in model_rows], dtype=float)
    low = means - np.array([row["cluster_ci_low"] for row in model_rows], dtype=float)
    high = np.array([row["cluster_ci_high"] for row in model_rows], dtype=float) - means
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(labels, means, color=["#315B7D", "#587C91", "#8A6D3B", "#A23E48"])
    ax.errorbar(labels, means, yerr=np.vstack([low, high]), fmt="none", ecolor="#111111", capsize=4)
    ax.set_ylabel("Primary error events per 100 words")
    ax.set_xlabel("Frozen local model artifact")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(output / "model_error_rates.png", dpi=240)
    plt.close(fig)
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
