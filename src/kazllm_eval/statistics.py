from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.stats import rankdata


@dataclass(frozen=True)
class PermutationResult:
    statistic: float
    p_value: float
    permutations: int


def _validate_matrix(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 2:
        raise ValueError("expected a two-dimensional matrix with at least two rows and columns")
    if not np.isfinite(matrix).all():
        raise ValueError("matrix contains missing or non-finite values")
    return matrix


def friedman_components(values: np.ndarray) -> tuple[float, float, np.ndarray]:
    matrix = _validate_matrix(values)
    n, k = matrix.shape
    ranks = np.vstack([rankdata(row, method="average") for row in matrix])
    rank_sums = ranks.sum(axis=0)
    uncorrected = 12.0 * np.square(rank_sums).sum() / (n * k * (k + 1)) - 3 * n * (k + 1)
    tie_sum = 0.0
    for row in matrix:
        _, counts = np.unique(row, return_counts=True)
        tie_sum += np.sum(counts**3 - counts)
    correction = 1.0 - tie_sum / (n * (k**3 - k))
    statistic = 0.0 if uncorrected == 0 else uncorrected / correction
    kendalls_w = statistic / (n * (k - 1))
    return float(statistic), float(kendalls_w), ranks


def friedman_permutation(
    values: np.ndarray,
    permutations: int = 99_999,
    seed: int = 2417,
    batch_size: int = 2_000,
) -> tuple[PermutationResult, float]:
    matrix = _validate_matrix(values)
    observed, kendalls_w, ranks = friedman_components(matrix)
    n, k = matrix.shape
    tie_sum = 0.0
    for row in matrix:
        _, counts = np.unique(row, return_counts=True)
        tie_sum += np.sum(counts**3 - counts)
    correction = 1.0 - tie_sum / (n * (k**3 - k))
    rng = np.random.default_rng(seed)
    extreme = 0
    remaining = permutations
    while remaining:
        size = min(batch_size, remaining)
        random_keys = rng.random((size, n, k))
        permutations_idx = np.argsort(random_keys, axis=2)
        permuted = np.take_along_axis(np.broadcast_to(ranks, (size, n, k)), permutations_idx, axis=2)
        rank_sums = permuted.sum(axis=1)
        statistics = 12.0 * np.square(rank_sums).sum(axis=1) / (n * k * (k + 1)) - 3 * n * (k + 1)
        if correction:
            statistics /= correction
        extreme += int(np.count_nonzero(statistics >= observed - 1e-12))
        remaining -= size
    p_value = (extreme + 1) / (permutations + 1)
    return PermutationResult(observed, p_value, permutations), kendalls_w


def pratt_signed_rank_permutation(
    left: Iterable[float],
    right: Iterable[float],
    permutations: int = 99_999,
    seed: int = 2417,
    batch_size: int = 5_000,
) -> PermutationResult:
    differences = np.asarray(list(left), dtype=float) - np.asarray(list(right), dtype=float)
    if differences.ndim != 1 or not len(differences):
        raise ValueError("paired vectors must be non-empty")
    if not np.isfinite(differences).all():
        raise ValueError("paired vectors contain missing or non-finite values")
    ranks = rankdata(np.abs(differences), method="average")
    nonzero = differences != 0
    signed_ranks = ranks[nonzero] * np.sign(differences[nonzero])
    observed = float(signed_ranks.sum())
    if not len(signed_ranks):
        return PermutationResult(0.0, 1.0, permutations)
    rng = np.random.default_rng(seed)
    extreme = 0
    remaining = permutations
    while remaining:
        size = min(batch_size, remaining)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(size, len(signed_ranks)))
        statistics = (signs * np.abs(signed_ranks)).sum(axis=1)
        extreme += int(np.count_nonzero(np.abs(statistics) >= abs(observed) - 1e-12))
        remaining -= size
    return PermutationResult(observed, (extreme + 1) / (permutations + 1), permutations)


def rank_biserial(left: Iterable[float], right: Iterable[float]) -> float:
    differences = np.asarray(list(left), dtype=float) - np.asarray(list(right), dtype=float)
    ranks = rankdata(np.abs(differences), method="average")
    nonzero = differences != 0
    denominator = ranks[nonzero].sum()
    if denominator == 0:
        return 0.0
    positive = ranks[(differences > 0)].sum()
    negative = ranks[(differences < 0)].sum()
    return float((positive - negative) / denominator)


def holm_adjust(p_values: Iterable[float]) -> list[float]:
    values = np.asarray(list(p_values), dtype=float)
    if np.any((values < 0) | (values > 1)):
        raise ValueError("p-values must lie in [0, 1]")
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    m = len(values)
    for position, index in enumerate(order):
        running = max(running, (m - position) * values[index])
        adjusted[index] = min(running, 1.0)
    return adjusted.tolist()


def stratified_prompt_bootstrap_difference(
    values: np.ndarray,
    strata: Iterable[str],
    left_index: int,
    right_index: int,
    replicates: int = 10_000,
    seed: int = 2417,
) -> dict[str, float]:
    matrix = _validate_matrix(values)
    strata_array = np.asarray(list(strata))
    if len(strata_array) != len(matrix):
        raise ValueError("one stratum label is required per prompt block")
    observed = float(np.mean(matrix[:, left_index] - matrix[:, right_index]))
    groups = [np.flatnonzero(strata_array == label) for label in np.unique(strata_array)]
    rng = np.random.default_rng(seed)
    estimates = np.empty(replicates)
    for replicate in range(replicates):
        sampled = np.concatenate([rng.choice(group, size=len(group), replace=True) for group in groups])
        estimates[replicate] = np.mean(matrix[sampled, left_index] - matrix[sampled, right_index])
    low, high = np.quantile(estimates, [0.025, 0.975])
    return {"difference": observed, "ci_low": float(low), "ci_high": float(high), "replicates": replicates}
