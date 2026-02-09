"""Fuzzy matching utilities for comparing extracted vs ground truth strings."""

from __future__ import annotations

from typing import Callable


def token_overlap_similarity(a: str, b: str) -> float:
    """Jaccard similarity on lowercased word tokens."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def best_match(
    candidate: str,
    references: list[str],
    similarity_fn: Callable[[str, str], float] = token_overlap_similarity,
    threshold: float = 0.5,
) -> tuple[str | None, float]:
    """Find the best matching reference for a candidate string.

    Returns (matched_reference, similarity_score) or (None, 0.0).
    """
    best_ref = None
    best_score = 0.0
    for ref in references:
        score = similarity_fn(candidate, ref)
        if score > best_score:
            best_score = score
            best_ref = ref
    if best_score >= threshold:
        return best_ref, best_score
    return None, 0.0


def compute_fuzzy_precision_recall(
    extracted: list[str],
    ground_truth: list[str],
    similarity_fn: Callable[[str, str], float] = token_overlap_similarity,
    threshold: float = 0.5,
) -> tuple[float, float, float, list[tuple[str, str, float]]]:
    """Compute precision, recall, F1 using greedy 1:1 fuzzy matching.

    Returns (precision, recall, f1, matched_pairs) where matched_pairs
    is a list of (extracted_item, ground_truth_item, similarity_score).
    """
    if not extracted and not ground_truth:
        return 1.0, 1.0, 1.0, []
    if not extracted:
        return 0.0, 0.0, 0.0, []
    if not ground_truth:
        return 0.0, 1.0, 0.0, []

    # Build similarity matrix
    pairs: list[tuple[float, int, int]] = []
    for i, ext in enumerate(extracted):
        for j, gt in enumerate(ground_truth):
            score = similarity_fn(ext, gt)
            if score >= threshold:
                pairs.append((score, i, j))

    # Greedy 1:1 matching by descending similarity
    pairs.sort(key=lambda x: x[0], reverse=True)
    used_extracted: set[int] = set()
    used_gt: set[int] = set()
    matched: list[tuple[str, str, float]] = []

    for score, i, j in pairs:
        if i not in used_extracted and j not in used_gt:
            matched.append((extracted[i], ground_truth[j], score))
            used_extracted.add(i)
            used_gt.add(j)

    n_matched = len(matched)
    p = n_matched / len(extracted) if extracted else 0.0
    r = n_matched / len(ground_truth) if ground_truth else 0.0
    f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    return p, r, f, matched
