"""Unit tests for the evaluation module — no API calls required."""

import math

import pytest

from customer_intelligence.evaluation.fuzzy_matching import (
    compute_fuzzy_precision_recall,
    token_overlap_similarity,
)
from customer_intelligence.evaluation.metrics import (
    f1,
    mean_absolute_error,
    ordinal_agreement,
    precision,
    precision_recall_f1,
    recall,
    score_distribution_stats,
)
from customer_intelligence.evaluation.report import (
    CorpusReport,
    EvaluationReport,
    JudgeScore,
    LayerReport,
    SignalMetrics,
)
from customer_intelligence.evaluation.structural_checks import (
    check_score_distribution,
    check_timeline_consistency,
    validate_utterance_indices,
)
from customer_intelligence.schemas.surface import TopicDetection
from customer_intelligence.schemas.transcript import Utterance


# ── Metrics ──────────────────────────────────────────────────────────────


class TestPrecision:
    def test_perfect(self):
        assert precision({"a", "b"}, {"a", "b"}) == 1.0

    def test_no_overlap(self):
        assert precision({"a"}, {"b"}) == 0.0

    def test_partial(self):
        assert precision({"a", "b", "c"}, {"a", "b"}) == pytest.approx(2 / 3)

    def test_empty_predicted_empty_actual(self):
        assert precision(set(), set()) == 1.0

    def test_empty_predicted_nonempty_actual(self):
        assert precision(set(), {"a"}) == 0.0

    def test_nonempty_predicted_empty_actual(self):
        assert precision({"a"}, set()) == 0.0


class TestRecall:
    def test_perfect(self):
        assert recall({"a", "b"}, {"a", "b"}) == 1.0

    def test_no_overlap(self):
        assert recall({"a"}, {"b"}) == 0.0

    def test_partial(self):
        assert recall({"a"}, {"a", "b"}) == 0.5

    def test_empty_actual(self):
        assert recall({"a"}, set()) == 1.0

    def test_empty_both(self):
        assert recall(set(), set()) == 1.0


class TestF1:
    def test_perfect(self):
        assert f1(1.0, 1.0) == 1.0

    def test_zero_both(self):
        assert f1(0.0, 0.0) == 0.0

    def test_harmonic_mean(self):
        assert f1(0.5, 1.0) == pytest.approx(2 / 3)


class TestPrecisionRecallF1:
    def test_combined(self):
        p, r, f = precision_recall_f1({"a", "b"}, {"a", "c"})
        assert p == 0.5
        assert r == 0.5
        assert f == 0.5


class TestMeanAbsoluteError:
    def test_perfect(self):
        assert mean_absolute_error([0.5, 0.8], [0.5, 0.8]) == 0.0

    def test_known_error(self):
        assert mean_absolute_error([0.5, 1.0], [0.3, 0.8]) == pytest.approx(0.2)

    def test_empty(self):
        assert math.isnan(mean_absolute_error([], []))

    def test_mismatched_lengths(self):
        assert math.isnan(mean_absolute_error([0.5], [0.3, 0.8]))


class TestOrdinalAgreement:
    def test_exact_match(self):
        assert ordinal_agreement("low", "low", ["low", "medium", "high"]) == 1.0

    def test_one_step(self):
        assert ordinal_agreement("low", "medium", ["low", "medium", "high"]) == 0.5

    def test_max_disagreement(self):
        assert ordinal_agreement("low", "high", ["low", "medium", "high"]) == 0.0

    def test_unknown_value(self):
        assert ordinal_agreement("unknown", "low", ["low", "medium", "high"]) == 0.0

    def test_single_value_scale(self):
        assert ordinal_agreement("low", "low", ["low"]) == 1.0


class TestScoreDistributionStats:
    def test_empty(self):
        stats = score_distribution_stats([])
        assert math.isnan(stats["mean"])
        assert stats["n"] == 0

    def test_uniform(self):
        stats = score_distribution_stats([0.1, 0.3, 0.5, 0.7, 0.9])
        assert stats["n"] == 5
        assert stats["mean"] == 0.5

    def test_all_same(self):
        stats = score_distribution_stats([0.8, 0.8, 0.8])
        assert stats["std"] == 0.0


# ── Fuzzy Matching ───────────────────────────────────────────────────────


class TestTokenOverlapSimilarity:
    def test_identical(self):
        assert token_overlap_similarity("pricing", "pricing") == 1.0

    def test_case_insensitive(self):
        assert token_overlap_similarity("Pricing", "pricing") == 1.0

    def test_partial_overlap(self):
        assert token_overlap_similarity("pricing negotiation", "pricing") == 0.5

    def test_no_overlap(self):
        assert token_overlap_similarity("pricing", "integration") == 0.0

    def test_empty_strings(self):
        assert token_overlap_similarity("", "") == 1.0

    def test_one_empty(self):
        assert token_overlap_similarity("pricing", "") == 0.0

    def test_multi_word(self):
        sim = token_overlap_similarity("ROI justification", "ROI analysis")
        assert sim == pytest.approx(1 / 3)


class TestComputeFuzzyPrecisionRecall:
    def test_perfect_match(self):
        p, r, f, matched = compute_fuzzy_precision_recall(
            ["pricing", "product"], ["pricing", "product"],
            threshold=0.8,
        )
        assert p == 1.0
        assert r == 1.0
        assert f == 1.0
        assert len(matched) == 2

    def test_no_match(self):
        p, r, f, matched = compute_fuzzy_precision_recall(
            ["pricing"], ["integration"],
            threshold=0.5,
        )
        assert p == 0.0
        assert r == 0.0
        assert f == 0.0
        assert len(matched) == 0

    def test_partial_match(self):
        p, r, f, matched = compute_fuzzy_precision_recall(
            ["pricing", "support"], ["pricing", "integration"],
            threshold=0.5,
        )
        assert p == 0.5
        assert r == 0.5
        assert len(matched) == 1

    def test_both_empty(self):
        p, r, f, matched = compute_fuzzy_precision_recall([], [])
        assert p == 1.0
        assert r == 1.0

    def test_extracted_empty(self):
        p, r, f, matched = compute_fuzzy_precision_recall([], ["a"])
        assert p == 0.0
        assert r == 0.0

    def test_ground_truth_empty(self):
        p, r, f, matched = compute_fuzzy_precision_recall(["a"], [])
        assert p == 0.0
        assert r == 1.0

    def test_one_to_one_matching(self):
        """Each extracted item should match at most one ground truth item."""
        p, r, f, matched = compute_fuzzy_precision_recall(
            ["pricing", "pricing strategy"],
            ["pricing"],
            threshold=0.4,
        )
        assert len(matched) == 1  # Only one GT item, so max 1 match
        assert r == 1.0
        assert p == 0.5

    def test_threshold_filtering(self):
        """Items below threshold should not match."""
        p, r, f, matched = compute_fuzzy_precision_recall(
            ["ROI justification"], ["ROI analysis"],
            threshold=0.5,  # similarity is 1/3, below threshold
        )
        assert len(matched) == 0


# ── Structural Checks ────────────────────────────────────────────────────


class TestValidateUtteranceIndices:
    def test_valid_indices(self):
        assert validate_utterance_indices([0, 5, 10], 10) == []

    def test_negative_index(self):
        issues = validate_utterance_indices([-1, 5], 10, "test")
        assert len(issues) == 1
        assert "-1" in issues[0]

    def test_exceeds_max(self):
        issues = validate_utterance_indices([5, 15], 10, "test")
        assert len(issues) == 1
        assert "15" in issues[0]


class TestCheckTimelineConsistency:
    def _make_utterances(self, n: int) -> list[Utterance]:
        return [
            Utterance(speaker="rep", text=f"turn {i}", turn_index=i)
            for i in range(n)
        ]

    def test_consistent_early(self):
        utterances = self._make_utterances(30)
        utterances[2] = Utterance(speaker="rep", text="pricing discussion", turn_index=2)
        topics = [TopicDetection(name="pricing", timeline_position="early", relevance=0.8)]
        assert check_timeline_consistency(topics, utterances) == []

    def test_inconsistent(self):
        utterances = self._make_utterances(30)
        utterances[25] = Utterance(speaker="rep", text="pricing discussion", turn_index=25)
        topics = [TopicDetection(name="pricing", timeline_position="early", relevance=0.8)]
        issues = check_timeline_consistency(topics, utterances)
        assert len(issues) == 1
        assert "pricing" in issues[0].lower()

    def test_topic_not_in_text(self):
        """If topic isn't mentioned in text, no check is possible — not an issue."""
        utterances = self._make_utterances(10)
        topics = [TopicDetection(name="quantum physics", timeline_position="early", relevance=0.5)]
        assert check_timeline_consistency(topics, utterances) == []


class TestCheckScoreDistribution:
    def test_well_distributed(self):
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        result = check_score_distribution(scores, "test")
        assert result["issues"] == []

    def test_low_variance(self):
        scores = [0.8, 0.81, 0.79, 0.8, 0.8]
        result = check_score_distribution(scores, "test")
        assert any("variance" in i for i in result["issues"])

    def test_single_bucket(self):
        scores = [0.85, 0.9, 0.88, 0.92, 0.95]
        result = check_score_distribution(scores, "test")
        assert any("bucket" in i for i in result["issues"])


# ── Report Models ────────────────────────────────────────────────────────


class TestSignalMetrics:
    def test_creation(self):
        m = SignalMetrics(signal_name="test", precision=0.8, recall=0.6)
        assert m.f1 is None  # Not auto-computed
        assert m.count_extracted == 0

    def test_with_judge_scores(self):
        m = SignalMetrics(
            signal_name="test",
            judge_scores=[JudgeScore(score=4, justification="good")],
            mean_judge_score=4.0,
        )
        assert m.mean_judge_score == 4.0


class TestEvaluationReport:
    def _make_report(self) -> EvaluationReport:
        return EvaluationReport(
            transcript_id="test_call",
            surface=LayerReport(
                layer_name="Surface",
                signal_metrics=[
                    SignalMetrics(signal_name="topics", precision=0.8, recall=0.6, f1=0.686),
                ],
            ),
            behavioral=LayerReport(
                layer_name="Behavioral",
                signal_metrics=[
                    SignalMetrics(signal_name="objections", precision=1.0, recall=0.5, f1=0.667),
                ],
            ),
            psychographic=LayerReport(
                layer_name="Psychographic",
                signal_metrics=[
                    SignalMetrics(signal_name="mental_model", f1=1.0),
                ],
            ),
        )

    def test_overall_f1(self):
        report = self._make_report()
        assert report.overall_f1 == pytest.approx((0.686 + 0.667 + 1.0) / 3, rel=1e-2)

    def test_all_signal_metrics(self):
        report = self._make_report()
        assert len(report.all_signal_metrics) == 3

    def test_summary_output(self):
        report = self._make_report()
        summary = report.summary()
        assert "test_call" in summary
        assert "Surface" in summary
        assert "topics" in summary


class TestCorpusReport:
    def test_mean_metrics(self):
        report1 = EvaluationReport(
            transcript_id="call1",
            surface=LayerReport(
                layer_name="Surface",
                signal_metrics=[SignalMetrics(signal_name="topics", precision=0.8, recall=0.6, f1=0.686)],
            ),
            behavioral=LayerReport(layer_name="Behavioral"),
            psychographic=LayerReport(layer_name="Psychographic"),
        )
        report2 = EvaluationReport(
            transcript_id="call2",
            surface=LayerReport(
                layer_name="Surface",
                signal_metrics=[SignalMetrics(signal_name="topics", precision=0.6, recall=0.8, f1=0.686)],
            ),
            behavioral=LayerReport(layer_name="Behavioral"),
            psychographic=LayerReport(layer_name="Psychographic"),
        )
        corpus = CorpusReport(reports=[report1, report2])
        agg = corpus.mean_metrics_by_signal()
        assert "topics" in agg
        assert agg["topics"]["precision"] == pytest.approx(0.7)
        assert agg["topics"]["recall"] == pytest.approx(0.7)
