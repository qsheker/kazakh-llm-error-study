import numpy as np

from kazllm_eval.statistics import (
    friedman_components,
    friedman_permutation,
    holm_adjust,
    pratt_signed_rank_permutation,
    rank_biserial,
    stratified_prompt_bootstrap_difference,
)


def test_friedman_no_difference():
    values = np.ones((8, 4))
    statistic, w, _ = friedman_components(values)
    result, permutation_w = friedman_permutation(values, permutations=999, seed=1)
    assert statistic == 0
    assert w == 0
    assert result.p_value == 1
    assert permutation_w == 0


def test_friedman_detects_consistent_order():
    values = np.tile([1.0, 2.0, 3.0, 4.0], (12, 1))
    result, w = friedman_permutation(values, permutations=4_999, seed=2)
    assert w == 1.0
    assert result.p_value < 0.01


def test_pratt_and_rank_biserial_direction():
    left = [1, 1, 2, 2, 3, 3]
    right = [2, 2, 3, 3, 4, 4]
    result = pratt_signed_rank_permutation(left, right, permutations=4_999, seed=3)
    assert result.statistic < 0
    assert rank_biserial(left, right) == -1


def test_holm_is_monotonic_in_sorted_order():
    adjusted = holm_adjust([0.01, 0.03, 0.2])
    assert adjusted == [0.03, 0.06, 0.2]


def test_stratified_bootstrap_returns_direction():
    values = np.array([[1, 2], [2, 3], [4, 5], [5, 6]], dtype=float)
    result = stratified_prompt_bootstrap_difference(values, ["e", "e", "p", "p"], 0, 1, 999, 4)
    assert result["difference"] == -1
    assert result["ci_low"] == -1
    assert result["ci_high"] == -1
