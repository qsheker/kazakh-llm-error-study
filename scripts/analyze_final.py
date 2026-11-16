#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import fasttext
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kazllm_eval.annotation import (
    EVENT_CATEGORIES,
    RESPONSE_FLAGS,
    load_annotation_workbook,
    load_run_records,
    validate_blinded_manifest,
)
from kazllm_eval.core import sha256_file, word_tokens
from kazllm_eval.detectors import (
    binary_metrics,
    clustered_f1_difference,
    contains_latin,
    fasttext_predict_one,
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


def valid_review_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


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


def stratified_category_bootstrap(
    rows: list[dict],
    categories: tuple[str, ...],
    replicates: int,
    seed: int,
) -> tuple[dict[str, dict[str, float | None]], dict[str, dict[str, float | None]]]:
    prompt_ids = sorted({row["prompt_id"] for row in rows})
    prompt_index = {prompt_id: index for index, prompt_id in enumerate(prompt_ids)}
    words = np.zeros(len(prompt_ids), dtype=float)
    events = np.zeros((len(prompt_ids), len(categories)), dtype=float)
    task_by_prompt: dict[str, str] = {}
    response_rates = {category: [] for category in categories}
    for row in rows:
        index = prompt_index[row["prompt_id"]]
        words[index] += row["word_count"]
        task_by_prompt.setdefault(row["prompt_id"], row["task_type"])
        if row["word_count"]:
            for category_index, category in enumerate(categories):
                events[index, category_index] += row[category]
                response_rates[category].append(100 * row[category] / row["word_count"])
        else:
            for category_index, category in enumerate(categories):
                events[index, category_index] += row[category]
    strata = np.array([task_by_prompt[prompt_id] for prompt_id in prompt_ids])
    groups = [np.flatnonzero(strata == label) for label in np.unique(strata)]
    rng = np.random.default_rng(seed)
    estimates = np.empty((replicates, len(categories)), dtype=float)
    for replicate in range(replicates):
        sampled = np.concatenate([rng.choice(group, size=len(group), replace=True) for group in groups])
        sampled_words = words[sampled].sum()
        estimates[replicate] = (
            np.nan if sampled_words == 0 else 100 * events[sampled].sum(axis=0) / sampled_words
        )
    total_words = words.sum()
    summaries = {}
    for category_index, category in enumerate(categories):
        low, high = np.nanquantile(estimates[:, category_index], [0.025, 0.975])
        summaries[category] = {
            "pooled_rate_per_100_words": None
            if total_words == 0
            else float(100 * events[:, category_index].sum() / total_words),
            "mean_response_rate": float(np.mean(response_rates[category]))
            if response_rates[category]
            else None,
            "cluster_ci_low": float(low),
            "cluster_ci_high": float(high),
        }
    contrasts = {}
    code_index = categories.index("code_switching")
    for category_index, category in enumerate(categories):
        if category == "code_switching":
            continue
        values = estimates[:, code_index] - estimates[:, category_index]
        low, high = np.nanquantile(values, [0.025, 0.975])
        contrasts[f"code_switching_minus_{category}"] = {
            "difference": summaries["code_switching"]["pooled_rate_per_100_words"]
            - summaries[category]["pooled_rate_per_100_words"],
            "ci_low": float(low),
            "ci_high": float(high),
        }
    return summaries, contrasts


def stratified_difference_in_differences(
    matrix: np.ndarray,
    strata: list[str],
    left_index: int,
    right_index: int,
    replicates: int,
    seed: int,
) -> dict[str, float | int]:
    strata_array = np.asarray(strata)
    expected = {"educational", "public_information"}
    if set(strata_array) != expected:
        raise ValueError(f"difference-in-differences requires strata {sorted(expected)}")
    differences = matrix[:, left_index] - matrix[:, right_index]
    educational = np.flatnonzero(strata_array == "educational")
    public = np.flatnonzero(strata_array == "public_information")
    observed = float(differences[public].mean() - differences[educational].mean())
    rng = np.random.default_rng(seed)
    estimates = np.empty(replicates)
    for replicate in range(replicates):
        sampled_educational = rng.choice(educational, size=len(educational), replace=True)
        sampled_public = rng.choice(public, size=len(public), replace=True)
        estimates[replicate] = (
            differences[sampled_public].mean() - differences[sampled_educational].mean()
        )
    low, high = np.quantile(estimates, [0.025, 0.975])
    return {
        "public_minus_educational_model_difference": observed,
        "ci_low": float(low),
        "ci_high": float(high),
        "replicates": replicates,
    }


def matrix_from_event_counts(
    event_counts: dict[str, Counter],
    mapping: dict[str, dict[str, str]],
    by_private: dict[str, dict],
    model_order: list[str],
) -> tuple[np.ndarray, list[str]]:
    by_prompt: dict[str, dict[str, float | None]] = defaultdict(dict)
    task_by_prompt: dict[str, str] = {}
    for blind_id, map_row in mapping.items():
        record = by_private[map_row["private_response_id"]]
        count = sum(event_counts[blind_id][category] for category in PRIMARY_CATEGORIES)
        by_prompt[record["prompt_id"]][record["model_label"]] = (
            None if not record["word_count"] else 100 * count / record["word_count"]
        )
        task_by_prompt[record["prompt_id"]] = record["task_type"]
    complete = [
        prompt_id
        for prompt_id, rows in sorted(by_prompt.items())
        if set(rows) == set(model_order) and all(rows[model] is not None for model in model_order)
    ]
    matrix = np.array([[by_prompt[prompt][model] for model in model_order] for prompt in complete])
    return matrix, [task_by_prompt[prompt] for prompt in complete]


def friedman_summary(matrix: np.ndarray, permutations: int, seed: int) -> dict[str, float | int | None]:
    if matrix.ndim != 2 or len(matrix) < 2:
        return {"complete_prompt_blocks": len(matrix), "statistic": None, "p_value": None, "kendalls_w": None}
    test, kendalls_w = friedman_permutation(matrix, permutations=permutations, seed=seed)
    return {
        "complete_prompt_blocks": len(matrix),
        "statistic": test.statistic,
        "p_value": test.p_value,
        "kendalls_w": kendalls_w,
        "permutations": test.permutations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate final statistics from the reviewed joint-team gold workbook.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/final_test_v2"))
    parser.add_argument("--mapping", type=Path, default=Path("data/blinding/private_model_key.csv"))
    parser.add_argument(
        "--team-workbook",
        type=Path,
        default=Path("annotations/team_gold/final_test_v2__team_gold.xlsx"),
    )
    parser.add_argument(
        "--blinded-manifest",
        type=Path,
        default=Path("annotations/final_test_v2__blinded_manifest.json"),
    )
    parser.add_argument(
        "--review-log",
        type=Path,
        default=Path("annotations/team_gold/team_review_log.csv"),
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
    team_workbook_path = resolve(args.team_workbook)
    blinded_manifest_path = resolve(args.blinded_manifest)
    review_log_path = resolve(args.review_log)
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
    mapped_private_ids = {row["private_response_id"] for row in mapping_rows}
    if len(mapped_private_ids) != 240 or mapped_private_ids != set(by_private):
        raise SystemExit("private mapping must cover every immutable receipt exactly once")
    for row in mapping_rows:
        record = by_private.get(row["private_response_id"])
        if (
            record is None
            or record["response_sha256"] != row["response_sha256"]
            or record["prompt_id"] != row["prompt_id"]
            or record["model_label"] != row["model_label"]
        ):
            raise SystemExit(f"mapping does not match immutable receipt for {row['blind_id']}")

    team_workbook = load_annotation_workbook(team_workbook_path, expected_responses=240)
    blinded_manifest = json.loads(blinded_manifest_path.read_text(encoding="utf-8"))
    validate_blinded_manifest(team_workbook, blinded_manifest)
    response_rows = list(team_workbook["responses"].values())
    if {row["blind_id"] for row in response_rows} != set(mapping):
        raise SystemExit("team gold workbook must contain exactly the 240 mapped blind IDs")
    response_labels = {row["blind_id"]: row for row in response_rows}
    for blind_id, row in response_labels.items():
        for flag in RESPONSE_FLAGS:
            if row.get(flag) not in {"yes", "no"}:
                raise SystemExit(f"{blind_id}: final {flag} must be yes or no")
        if row["requirement_missing"] == "yes" and not row.get("missing_requirements", "").strip():
            raise SystemExit(f"{blind_id}: missing requirements must be named")

    review_rows = read_csv(review_log_path)
    reviewers = set(protocol["team"])
    if len(review_rows) != 240 or {row.get("blind_id") for row in review_rows} != set(mapping):
        raise SystemExit("team review log must contain exactly one row for every blind ID")
    assignment_counts = Counter(row.get("assigned_reviewer") for row in review_rows)
    if set(assignment_counts) != reviewers or set(assignment_counts.values()) != {80}:
        raise SystemExit("team review log must assign exactly 80 blind IDs to each team member")
    for row in review_rows:
        blind_id = row.get("blind_id", "")
        if row.get("review_status") != "approved":
            raise SystemExit(f"{blind_id}: review_status must be approved")
        if row.get("reviewer") not in reviewers:
            raise SystemExit(f"{blind_id}: reviewer must be a named team member")
        if row.get("reviewer") != row.get("assigned_reviewer"):
            raise SystemExit(f"{blind_id}: reviewer must match the balanced assignment")
        if row.get("ai_assistance") not in {"yes", "no"}:
            raise SystemExit(f"{blind_id}: ai_assistance must be yes or no")
        if not valid_review_timestamp(row.get("reviewed_utc", "").strip()):
            raise SystemExit(f"{blind_id}: reviewed_utc must be an ISO-8601 timestamp with timezone")

    event_rows = team_workbook["events"]
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
            start_token = int(row["start_token_one_based"])
            end_token = int(row["end_token_one_based"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"{blind_id}: event offsets and token indices must be integers") from exc
        if (
            start < 0
            or end <= start
            or end > len(record["response_text"])
            or record["response_text"][start:end] != row.get("exact_fragment", "")
        ):
            raise SystemExit(f"{blind_id}: final event fragment does not match immutable response")
        token_count = len(word_tokens(record["response_text"]))
        if start_token < 1 or end_token < start_token or end_token > token_count:
            raise SystemExit(f"{blind_id}: final event token indices are outside the response")
        if not row.get("proposed_correction", "").strip() or not row.get("rationale", "").strip():
            raise SystemExit(f"{blind_id}: final event requires correction and annotation rationale")
        if row.get("needs_adjudication") != "no":
            raise SystemExit(f"{blind_id}: final event still needs adjudication")
        event_counts[blind_id][category] += 1

    metrics = []
    for blind_id, map_row in mapping.items():
        record = by_private[map_row["private_response_id"]]
        counts = event_counts[blind_id]
        primary_count = sum(counts[category] for category in PRIMARY_CATEGORIES)
        word_count = int(record["word_count"])
        rate = None if word_count == 0 else 100 * primary_count / word_count
        eval_count = record.get("eval_count")
        eval_duration_ns = record.get("eval_duration_ns")
        tokens_per_second = (
            None
            if not eval_count or not eval_duration_ns
            else float(eval_count) / (float(eval_duration_ns) / 1_000_000_000)
        )
        metrics.append(
            {
                "blind_id": blind_id,
                "private_response_id": record["private_response_id"],
                "prompt_id": record["prompt_id"],
                "task_type": record["task_type"],
                "model_label": record["model_label"],
                "word_count": word_count,
                "length_150_200": 150 <= word_count <= 200,
                "finish_reason": record["finish_reason"],
                "truncated": record["finish_reason"] == "length",
                "client_latency_ms": record.get("client_latency_ms"),
                "prompt_eval_count": record.get("prompt_eval_count"),
                "eval_count": eval_count,
                "tokens_per_second": tokens_per_second,
                **{category: counts[category] for category in EVENT_CATEGORIES},
                "primary_count": primary_count,
                "primary_error_present": primary_count > 0,
                "primary_rate_per_100_words": rate,
                "primary_plus_surface_rate_per_100_words": None
                if word_count == 0
                else 100 * (primary_count + counts["surface"]) / word_count,
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
    model_task_interactions = []
    for pair_index, (left_index, right_index) in enumerate(itertools.combinations(range(4), 2)):
        model_task_interactions.append(
            {
                "left": model_order[left_index],
                "right": model_order[right_index],
                **stratified_difference_in_differences(
                    matrix,
                    strata,
                    left_index,
                    right_index,
                    replicates=bootstrap,
                    seed=seed + 701 + pair_index,
                ),
            }
        )

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
    alpha = float(protocol["analysis"]["alpha"])
    h1_supported = friedman.p_value < alpha
    h2_supported = h1_supported and h2_pair["p_holm"] < alpha and h2_difference < 0 and h2_high < 0

    general_models = {"qwen3_8b", "llama31_8b", "gemma3_12b"}
    general_rows = [row for row in metrics if row["model_label"] in general_models]
    h3_categories, h3_contrasts = stratified_category_bootstrap(
        general_rows,
        PRIMARY_CATEGORIES,
        replicates=bootstrap,
        seed=seed + 801,
    )
    h3_top = max(
        h3_categories,
        key=lambda key: h3_categories[key]["pooled_rate_per_100_words"]
        if h3_categories[key]["pooled_rate_per_100_words"] is not None
        else -1,
    )

    exemptions = {
        line.strip().casefold()
        for line in exemptions_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    lid = fasttext.load_model(str(lid_path))

    def predictor(text: str) -> tuple[str, float]:
        return fasttext_predict_one(lid, text)

    detector_rows = []
    for row in metrics:
        record = by_private[row["private_response_id"]]
        tokens = word_tokens(record["response_text"])
        nonexempt_latin = [
            token for token in tokens if token.casefold() not in exemptions and contains_latin(token)
        ]
        row["nonexempt_latin_token_share"] = (
            None if not tokens else len(nonexempt_latin) / len(tokens)
        )
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
                "nonexempt_latin_token_share": row["nonexempt_latin_token_share"],
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

    model_task_rows = []
    for model in model_order:
        for task_type in ("educational", "public_information"):
            subset = [
                row
                for row in metrics
                if row["model_label"] == model and row["task_type"] == task_type
            ]
            words = sum(row["word_count"] for row in subset)
            primary_events = sum(row["primary_count"] for row in subset)
            defined_rates = [
                row["primary_rate_per_100_words"]
                for row in subset
                if row["primary_rate_per_100_words"] is not None
            ]
            model_task_rows.append(
                {
                    "model": model,
                    "task_type": task_type,
                    "responses": len(subset),
                    "total_words": words,
                    "total_primary_events": primary_events,
                    "pooled_rate_per_100_words": None
                    if words == 0
                    else 100 * primary_events / words,
                    "mean_response_rate": float(np.mean(defined_rates)) if defined_rates else None,
                    "truncated_rate": float(np.mean([row["truncated"] for row in subset])),
                    "length_compliance_rate": float(
                        np.mean([row["length_150_200"] for row in subset])
                    ),
                    "mean_client_latency_ms": float(
                        np.mean(
                            [
                                row["client_latency_ms"]
                                for row in subset
                                if row["client_latency_ms"] is not None
                            ]
                        )
                    ),
                    "mean_tokens_per_second": float(
                        np.mean(
                            [
                                row["tokens_per_second"]
                                for row in subset
                                if row["tokens_per_second"] is not None
                            ]
                        )
                    ),
                    **{
                        f"{flag}_rate": float(np.mean([row[flag] == "yes" for row in subset]))
                        for flag in RESPONSE_FLAGS
                    },
                }
            )

    surface_matrix = np.array(
        [
            [
                by_prompt[prompt_id][model]["primary_plus_surface_rate_per_100_words"]
                for model in model_order
            ]
            for prompt_id in complete_prompts
        ],
        dtype=float,
    )
    nontruncated_prompts = [
        prompt_id
        for prompt_id in complete_prompts
        if not any(by_prompt[prompt_id][model]["truncated"] for model in model_order)
    ]
    nontruncated_matrix = np.array(
        [
            [by_prompt[prompt_id][model]["primary_rate_per_100_words"] for model in model_order]
            for prompt_id in nontruncated_prompts
        ],
        dtype=float,
    )
    sensitivity = {
        "exclude_truncated": friedman_summary(
            nontruncated_matrix,
            permutations=permutations,
            seed=seed + 901,
        ),
        "include_surface_errors": friedman_summary(
            surface_matrix,
            permutations=permutations,
            seed=seed + 902,
        ),
        "model_by_task_difference_in_differences": model_task_interactions,
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
        "h3": {
            "descriptive_top_category": h3_top,
            "category_summaries": h3_categories,
            "code_switching_contrasts": h3_contrasts,
        },
        "h4": h4,
        "models": model_rows,
        "pairwise": pairwise,
        "sensitivity": sensitivity,
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
    write_csv(output / "model_task_rates.csv", list(model_task_rows[0]), model_task_rows)
    write_csv(output / "detector_response_metrics.csv", list(detector_rows[0]), detector_rows)
    write_csv(
        output / "model_task_interactions.csv",
        list(model_task_interactions[0]),
        model_task_interactions,
    )
    write_json(output / "sensitivity.json", sensitivity)
    write_json(
        output / "input_hashes.json",
        {
            "run_manifest": sha256_file(run_dir / "manifest.json"),
            "private_mapping": sha256_file(mapping_path),
            "team_gold_workbook": sha256_file(team_workbook_path),
            "blinded_manifest": sha256_file(blinded_manifest_path),
            "team_review_log": sha256_file(review_log_path),
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
