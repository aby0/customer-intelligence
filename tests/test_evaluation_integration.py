"""Integration tests for evaluation pipeline — maps to spec acceptance criteria.

These tests require LLM API calls (for extraction) and ground truth data.
Run with: pytest tests/test_evaluation_integration.py -m integration
"""

import json
from pathlib import Path

import pytest

from customer_intelligence.evaluation import evaluate, evaluate_corpus
from customer_intelligence.evaluation.report import EvaluationReport
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.transcript import Transcript

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

pytestmark = pytest.mark.integration


def _load_test_triples() -> list[tuple[Transcript, ExtractionResult, ExtractionResult]]:
    """Load transcript + ground truth pairs, then run extraction for each."""
    triples = []
    for tf in sorted(TRANSCRIPTS_DIR.glob("*.json")):
        gt_file = GROUND_TRUTH_DIR / tf.name
        if gt_file.exists():
            transcript = Transcript.model_validate_json(tf.read_text())
            ground_truth = ExtractionResult.model_validate_json(gt_file.read_text())
            triples.append((transcript, ground_truth))
    return triples


@pytest.fixture(scope="module")
def test_triples():
    """Load transcript + ground truth pairs and run extraction."""
    pairs = _load_test_triples()
    if len(pairs) < 3:
        pytest.skip("Need at least 3 transcript/ground truth pairs — run generator first")

    from customer_intelligence.extraction.extractor import extract

    triples = []
    for transcript, ground_truth in pairs:
        extracted = extract(transcript)
        triples.append((extracted, ground_truth, transcript))
    return triples


@pytest.fixture(scope="module")
def evaluation_reports(test_triples) -> list[EvaluationReport]:
    """Run evaluation on each extracted/ground truth pair."""
    reports = []
    for extracted, ground_truth, transcript in test_triples:
        report = evaluate(extracted, ground_truth, transcript, skip_llm_judge=True)
        reports.append(report)
    return reports


class TestEvaluationAcceptanceCriteria:
    """Tests mapping directly to spec acceptance criteria for Evaluation.

    From spec/features/2026-02-07-signal-extraction.md:
    - [ ] Extraction quality is evaluated against a human-annotated golden set (at least 3 transcripts)
    - [ ] Evaluation covers precision and recall for each signal type independently
    """

    def test_evaluated_against_golden_set(self, evaluation_reports):
        """AC: Extraction quality evaluated against human-annotated golden set (≥3 transcripts)."""
        assert len(evaluation_reports) >= 3, (
            f"Only {len(evaluation_reports)} transcripts evaluated, need at least 3"
        )
        for report in evaluation_reports:
            assert report.overall_f1 >= 0.0, (
                f"Evaluation failed to produce results for {report.transcript_id}"
            )

    def test_precision_and_recall_per_signal_type(self, evaluation_reports):
        """AC: Evaluation covers precision and recall for each signal type independently."""
        required_signals = {
            "aspects", "topics", "entities", "key_phrases",
            "objection_triples", "buying_intent", "competitive_mentions",
            "engagement_trajectory", "mental_model", "persona_indicators",
            "language_fingerprint",
        }

        for report in evaluation_reports:
            found_signals = set()
            for m in report.all_signal_metrics:
                found_signals.add(m.signal_name)
                assert m.precision is not None, (
                    f"Missing precision for {m.signal_name} in {report.transcript_id}"
                )
                assert m.recall is not None, (
                    f"Missing recall for {m.signal_name} in {report.transcript_id}"
                )

            missing = required_signals - found_signals
            assert not missing, (
                f"Missing signal types in {report.transcript_id}: {missing}"
            )


class TestSurfaceEvaluation:
    """Evaluate Layer 1 extraction quality with precision and recall."""

    def test_topic_quality(self, evaluation_reports):
        for report in evaluation_reports:
            topics = next(
                m for m in report.surface.signal_metrics if m.signal_name == "topics"
            )
            assert topics.recall >= 0.3, (
                f"Topic recall too low for {report.transcript_id}: {topics.recall:.0%}"
            )

    def test_entity_quality(self, evaluation_reports):
        for report in evaluation_reports:
            entities = next(
                m for m in report.surface.signal_metrics if m.signal_name == "entities"
            )
            assert entities.recall >= 0.3, (
                f"Entity recall too low for {report.transcript_id}: {entities.recall:.0%}"
            )

    def test_aspect_has_polarity_accuracy(self, evaluation_reports):
        for report in evaluation_reports:
            aspects = next(
                m for m in report.surface.signal_metrics if m.signal_name == "aspects"
            )
            if aspects.accuracy is not None:
                assert aspects.accuracy >= 0.3, (
                    f"Aspect polarity accuracy too low for {report.transcript_id}"
                )


class TestBehavioralEvaluation:
    """Evaluate Layer 2 extraction quality with precision and recall."""

    def test_objection_type_quality(self, evaluation_reports):
        for report in evaluation_reports:
            objections = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "objection_triples"
            )
            assert objections.recall >= 0.3, (
                f"Objection recall too low for {report.transcript_id}: {objections.recall:.0%}"
            )

    def test_buying_intent_quality(self, evaluation_reports):
        for report in evaluation_reports:
            intent = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "buying_intent"
            )
            # If ground truth has intent markers, extraction should find some
            if intent.count_ground_truth > 0:
                assert intent.count_extracted > 0, (
                    f"No buying intent markers found for {report.transcript_id}"
                )


class TestPsychographicEvaluation:
    """Evaluate Layer 3 extraction quality."""

    def test_mental_model_accuracy(self, evaluation_reports):
        matches = 0
        total = len(evaluation_reports)
        for report in evaluation_reports:
            mm = next(
                m for m in report.psychographic.signal_metrics
                if m.signal_name == "mental_model"
            )
            if mm.accuracy and mm.accuracy >= 0.5:
                matches += 1
        assert matches / total >= 0.5 if total else True, (
            f"Mental model accuracy: {matches}/{total}"
        )

    def test_persona_detection(self, evaluation_reports):
        for report in evaluation_reports:
            personas = next(
                m for m in report.psychographic.signal_metrics
                if m.signal_name == "persona_indicators"
            )
            if personas.count_ground_truth > 0:
                assert personas.recall > 0, (
                    f"No persona match for {report.transcript_id}"
                )


class TestMultimodalEvaluation:
    """Evaluate multimodal divergence detection."""

    def test_divergence_when_expected(self, evaluation_reports):
        for report in evaluation_reports:
            if report.multimodal is None:
                continue
            divergences = next(
                (m for m in report.multimodal.signal_metrics if m.signal_name == "divergences"),
                None,
            )
            if divergences and divergences.count_ground_truth > 0:
                assert divergences.count_extracted > 0, (
                    f"No divergences found for {report.transcript_id}"
                )


@pytest.mark.slow
class TestLLMJudgeScoring:
    """Test LLM-as-judge scoring (slow — multiple API calls per transcript)."""

    def test_judge_scores_produced(self, test_triples):
        """Run evaluation with LLM judge on first transcript and verify scores."""
        extracted, ground_truth, transcript = test_triples[0]
        report = evaluate(
            extracted, ground_truth, transcript, skip_llm_judge=False,
        )

        # At least some signals should have judge scores
        signals_with_judges = [
            m for m in report.all_signal_metrics if m.judge_scores
        ]
        assert len(signals_with_judges) > 0, "No LLM judge scores produced"

        for m in signals_with_judges:
            assert m.mean_judge_score is not None
            assert 1.0 <= m.mean_judge_score <= 5.0
