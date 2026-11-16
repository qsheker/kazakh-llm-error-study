from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np

from .core import word_tokens


def contains_latin(token: str) -> bool:
    return any("LATIN" in unicodedata.name(character, "") for character in token)


def latin_response_positive(text: str, exemptions: Iterable[str] = ()) -> bool:
    exempt = {item.casefold() for item in exemptions}
    return any(token.casefold() not in exempt and contains_latin(token) for token in word_tokens(text))


def sentence_and_three_word_windows(text: str) -> list[str]:
    spans = [match.group().strip() for match in re.finditer(r"[^.!?\n]+[.!?]?", text) if match.group().strip()]
    windows = []
    for span in spans:
        tokens = word_tokens(span)
        windows.extend(" ".join(tokens[index : index + 3]) for index in range(max(0, len(tokens) - 2)))
    return spans + windows


@dataclass(frozen=True)
class LanguagePrediction:
    text: str
    language: str
    confidence: float


def fasttext_predict_one(model: Any, text: str) -> tuple[str, float]:
    """Return one fastText prediction without the NumPy-2-incompatible wrapper.

    fasttext-wheel 0.9.2 calls ``np.array(..., copy=False)`` in its public
    ``predict`` method, which raises with NumPy 2. The bound native predictor
    returns the same probability/label pairs before that conversion.
    """
    normalized = text.replace("\n", " ").strip() + "\n"
    predictions = model.f.predict(normalized, 1, 0.0, "strict")
    if not predictions:
        raise ValueError("fastText returned no language prediction")
    probability, label = predictions[0]
    return str(label).removeprefix("__label__"), float(probability)


def fasttext_response_positive(
    text: str,
    predictor: Callable[[str], tuple[str, float]],
    threshold: float = 0.85,
    exemptions: Iterable[str] = (),
) -> tuple[bool, list[LanguagePrediction]]:
    exempt = {item.casefold() for item in exemptions}
    predictions = []
    positive = False
    for window in sentence_and_three_word_windows(text):
        tokens = word_tokens(window)
        # Case is not an exemption: all-caps foreign prose is still a possible
        # code-switch. Only the frozen explicit exemption list is removed.
        meaningful = [token for token in tokens if token.casefold() not in exempt]
        if len(meaningful) < 3 or sum(map(len, meaningful)) < 12:
            continue
        evaluated_text = " ".join(meaningful)
        language, confidence = predictor(evaluated_text)
        predictions.append(LanguagePrediction(evaluated_text, language, confidence))
        if language != "kk" and confidence >= threshold:
            positive = True
    return positive, predictions


def binary_metrics(predicted: Iterable[bool], gold: Iterable[bool]) -> dict[str, float | int | None]:
    p = np.asarray(list(predicted), dtype=bool)
    g = np.asarray(list(gold), dtype=bool)
    if p.shape != g.shape or p.ndim != 1:
        raise ValueError("predicted and gold must be same-length vectors")
    tp = int(np.sum(p & g))
    fp = int(np.sum(p & ~g))
    fn = int(np.sum(~p & g))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def clustered_f1_difference(
    latin: Iterable[bool],
    hybrid: Iterable[bool],
    gold: Iterable[bool],
    prompt_ids: Iterable[str],
    replicates: int = 10_000,
    seed: int = 2417,
) -> dict[str, float | int | None]:
    latin_array = np.asarray(list(latin), dtype=bool)
    hybrid_array = np.asarray(list(hybrid), dtype=bool)
    gold_array = np.asarray(list(gold), dtype=bool)
    prompt_array = np.asarray(list(prompt_ids))
    if not (len(latin_array) == len(hybrid_array) == len(gold_array) == len(prompt_array)):
        raise ValueError("all response-level vectors must have equal length")
    latin_f1 = binary_metrics(latin_array, gold_array)["f1"]
    hybrid_f1 = binary_metrics(hybrid_array, gold_array)["f1"]
    observed = None if latin_f1 is None or hybrid_f1 is None else hybrid_f1 - latin_f1
    unique_prompts = np.unique(prompt_array)
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(replicates):
        sampled_prompts = rng.choice(unique_prompts, size=len(unique_prompts), replace=True)
        indices = np.concatenate([np.flatnonzero(prompt_array == prompt) for prompt in sampled_prompts])
        lf = binary_metrics(latin_array[indices], gold_array[indices])["f1"]
        hf = binary_metrics(hybrid_array[indices], gold_array[indices])["f1"]
        if lf is not None and hf is not None:
            estimates.append(hf - lf)
    if not estimates:
        return {"difference": observed, "ci_low": None, "ci_high": None, "valid_replicates": 0}
    low, high = np.quantile(estimates, [0.025, 0.975])
    return {
        "difference": observed,
        "ci_low": float(low),
        "ci_high": float(high),
        "valid_replicates": len(estimates),
    }
