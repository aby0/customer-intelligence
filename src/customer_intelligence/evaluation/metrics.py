"""Core metric functions: precision, recall, F1, MAE, ordinal agreement, distribution stats."""

from __future__ import annotations

import math


def precision(predicted: set, actual: set) -> float:
    """Fraction of predicted items that are correct."""
    if not predicted:
        return 1.0 if not actual else 0.0
    return len(predicted & actual) / len(predicted)


def recall(predicted: set, actual: set) -> float:
    """Fraction of actual items that were found."""
    if not actual:
        return 1.0
    return len(predicted & actual) / len(actual)


def f1(p: float, r: float) -> float:
    """Harmonic mean of precision and recall."""
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def precision_recall_f1(predicted: set, actual: set) -> tuple[float, float, float]:
    """Compute precision, recall, and F1 in one call."""
    p = precision(predicted, actual)
    r = recall(predicted, actual)
    return p, r, f1(p, r)


def mean_absolute_error(predicted: list[float], actual: list[float]) -> float:
    """Mean absolute error between two aligned score lists."""
    if not predicted or len(predicted) != len(actual):
        return float("nan")
    return sum(abs(p - a) for p, a in zip(predicted, actual)) / len(predicted)


def ordinal_agreement(predicted: str, actual: str, scale: list[str]) -> float:
    """Agreement score for ordered categorical values.

    Returns 1.0 for exact match, 0.0 for maximum disagreement.
    """
    if predicted not in scale or actual not in scale:
        return 0.0
    max_dist = len(scale) - 1
    if max_dist == 0:
        return 1.0
    dist = abs(scale.index(predicted) - scale.index(actual))
    return 1.0 - dist / max_dist


def score_distribution_stats(scores: list[float]) -> dict:
    """Compute distribution statistics for a list of 0-1 scores.

    Returns mean, std, and bucket counts for detecting degenerate outputs.
    """
    if not scores:
        return {"mean": float("nan"), "std": float("nan"), "buckets": {}, "n": 0}

    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    std = math.sqrt(variance)

    buckets = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for s in scores:
        if s < 0.2:
            buckets["0.0-0.2"] += 1
        elif s < 0.4:
            buckets["0.2-0.4"] += 1
        elif s < 0.6:
            buckets["0.4-0.6"] += 1
        elif s < 0.8:
            buckets["0.6-0.8"] += 1
        else:
            buckets["0.8-1.0"] += 1

    return {"mean": round(mean, 4), "std": round(std, 4), "buckets": buckets, "n": n}
