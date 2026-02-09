"""Programmatic structural validation for extraction outputs."""

from __future__ import annotations

from customer_intelligence.schemas.surface import TopicDetection
from customer_intelligence.schemas.transcript import Utterance

from .metrics import score_distribution_stats


def validate_utterance_indices(
    indices: list[int], max_index: int, label: str = "",
) -> list[str]:
    """Check that utterance indices are valid (non-negative, within bounds)."""
    issues = []
    for idx in indices:
        if idx < 0:
            issues.append(f"{label}: negative index {idx}")
        elif idx > max_index:
            issues.append(f"{label}: index {idx} exceeds max {max_index}")
    return issues


def check_timeline_consistency(
    topics: list[TopicDetection],
    utterances: list[Utterance],
) -> list[str]:
    """Verify that topic timeline positions are consistent with the transcript.

    Searches for topic name mentions in utterance text, computes the median
    position, and checks if the labeled timeline_position matches the third
    of the transcript where mentions concentrate.
    """
    if not utterances:
        return []

    total_turns = len(utterances)
    issues = []

    for topic in topics:
        # Find utterances that mention this topic (case-insensitive)
        topic_lower = topic.name.lower()
        mention_indices = [
            u.turn_index
            for u in utterances
            if topic_lower in u.text.lower()
        ]

        if not mention_indices:
            # Topic not found in text — can't verify, not an issue per se
            continue

        median_idx = sorted(mention_indices)[len(mention_indices) // 2]
        third = total_turns / 3

        if median_idx < third:
            expected = "early"
        elif median_idx < 2 * third:
            expected = "mid"
        else:
            expected = "late"

        if topic.timeline_position != expected:
            issues.append(
                f"Topic '{topic.name}': labeled '{topic.timeline_position}' "
                f"but mentions concentrate in '{expected}' "
                f"(median turn {median_idx}/{total_turns})"
            )

    return issues


def check_score_distribution(
    scores: list[float], label: str,
) -> dict:
    """Analyze score distribution and flag degenerate patterns.

    Returns stats dict with an added 'issues' key listing problems.
    """
    stats = score_distribution_stats(scores)
    issues = []

    if stats["n"] >= 3:
        # Flag if all scores are nearly identical
        if stats["std"] < 0.05:
            issues.append(
                f"{label}: very low variance (std={stats['std']:.3f}) — "
                f"scores may not be well-calibrated"
            )

        # Flag if all scores cluster in a single bucket
        non_empty_buckets = sum(1 for v in stats["buckets"].values() if v > 0)
        if non_empty_buckets == 1 and stats["n"] >= 5:
            bucket = next(k for k, v in stats["buckets"].items() if v > 0)
            issues.append(
                f"{label}: all {stats['n']} scores in bucket {bucket}"
            )

    stats["issues"] = issues
    return stats
