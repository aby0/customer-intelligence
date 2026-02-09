"""Extraction accuracy tests against ground truth.

These are integration tests that require LLM API calls.
Run with: pytest tests/test_extraction.py -m integration

Uses the evaluation module for precision/recall/F1 metrics with fuzzy matching.
"""

from pathlib import Path

import pytest

from customer_intelligence.evaluation import evaluate
from customer_intelligence.evaluation.report import EvaluationReport
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.transcript import Transcript

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def _load_test_cases() -> list[tuple[Transcript, ExtractionResult]]:
    """Load transcript + ground truth pairs."""
    pairs = []
    for tf in sorted(TRANSCRIPTS_DIR.glob("*.json")):
        gt_file = GROUND_TRUTH_DIR / tf.name
        if gt_file.exists():
            transcript = Transcript.model_validate_json(tf.read_text())
            ground_truth = ExtractionResult.model_validate_json(gt_file.read_text())
            pairs.append((transcript, ground_truth))
    return pairs


@pytest.fixture(scope="module")
def test_cases() -> list[tuple[Transcript, ExtractionResult]]:
    cases = _load_test_cases()
    if not cases:
        pytest.skip("No transcript/ground truth pairs found — run generator first")
    return cases


@pytest.fixture(scope="module")
def extracted_results(
    test_cases: list[tuple[Transcript, ExtractionResult]],
) -> list[tuple[ExtractionResult, ExtractionResult, Transcript]]:
    """Run extraction on each transcript and pair with ground truth."""
    from customer_intelligence.extraction.extractor import extract

    triples = []
    for transcript, ground_truth in test_cases:
        result = extract(transcript)
        triples.append((result, ground_truth, transcript))
    return triples


@pytest.fixture(scope="module")
def evaluation_reports(
    extracted_results: list[tuple[ExtractionResult, ExtractionResult, Transcript]],
) -> list[EvaluationReport]:
    """Run evaluation on each extracted/ground truth/transcript triple."""
    reports = []
    for result, ground_truth, transcript in extracted_results:
        report = evaluate(result, ground_truth, transcript, skip_llm_judge=True)
        reports.append(report)
    return reports


class TestSurfaceExtraction:
    """Evaluate Layer 1 extraction quality."""

    def test_topics_detected(self, evaluation_reports: list[EvaluationReport]):
        """Extracted topics should have reasonable recall."""
        for report in evaluation_reports:
            topics = next(
                m for m in report.surface.signal_metrics if m.signal_name == "topics"
            )
            assert topics.recall >= 0.5, (
                f"Topic recall too low for {report.transcript_id}: {topics.recall:.0%}"
            )

    def test_topics_precision(self, evaluation_reports: list[EvaluationReport]):
        """Extracted topics should have reasonable precision."""
        for report in evaluation_reports:
            topics = next(
                m for m in report.surface.signal_metrics if m.signal_name == "topics"
            )
            assert topics.precision >= 0.3, (
                f"Topic precision too low for {report.transcript_id}: {topics.precision:.0%}"
            )

    def test_entities_detected(self, evaluation_reports: list[EvaluationReport]):
        """Extracted entities should have reasonable recall."""
        for report in evaluation_reports:
            entities = next(
                m for m in report.surface.signal_metrics if m.signal_name == "entities"
            )
            assert entities.recall >= 0.5, (
                f"Entity recall too low for {report.transcript_id}: {entities.recall:.0%}"
            )

    def test_entities_precision(self, evaluation_reports: list[EvaluationReport]):
        """Extracted entities should have reasonable precision."""
        for report in evaluation_reports:
            entities = next(
                m for m in report.surface.signal_metrics if m.signal_name == "entities"
            )
            assert entities.precision >= 0.3, (
                f"Entity precision too low for {report.transcript_id}: {entities.precision:.0%}"
            )

    def test_aspect_sentiment_quality(self, evaluation_reports: list[EvaluationReport]):
        """Aspect-based sentiment should extract aspects with correct polarity."""
        for report in evaluation_reports:
            aspects = next(
                m for m in report.surface.signal_metrics if m.signal_name == "aspects"
            )
            if aspects.count_ground_truth > 0:
                assert aspects.recall >= 0.3, (
                    f"Aspect recall too low for {report.transcript_id}: {aspects.recall:.0%}"
                )

    def test_key_phrase_quality(self, evaluation_reports: list[EvaluationReport]):
        """Key phrases should have reasonable overlap with ground truth."""
        for report in evaluation_reports:
            kp = next(
                m for m in report.surface.signal_metrics if m.signal_name == "key_phrases"
            )
            if kp.count_ground_truth > 0:
                assert kp.recall >= 0.2, (
                    f"Key phrase recall too low for {report.transcript_id}: {kp.recall:.0%}"
                )


class TestBehavioralExtraction:
    """Evaluate Layer 2 extraction quality."""

    def test_objection_types_detected(self, evaluation_reports: list[EvaluationReport]):
        """Extracted objection types should match ground truth."""
        for report in evaluation_reports:
            objections = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "objection_triples"
            )
            if objections.count_ground_truth > 0:
                assert objections.recall >= 0.5, (
                    f"Objection type recall too low for {report.transcript_id}: "
                    f"{objections.recall:.0%}"
                )

    def test_objection_precision(self, evaluation_reports: list[EvaluationReport]):
        """Extraction should not hallucinate too many objection types."""
        for report in evaluation_reports:
            objections = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "objection_triples"
            )
            if objections.count_ground_truth > 0:
                assert objections.precision >= 0.3, (
                    f"Objection precision too low for {report.transcript_id}: "
                    f"{objections.precision:.0%}"
                )

    def test_buying_intent_detected(self, evaluation_reports: list[EvaluationReport]):
        """If ground truth has buying intent markers, extraction should find some."""
        for report in evaluation_reports:
            intent = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "buying_intent"
            )
            if intent.count_ground_truth > 0:
                assert intent.count_extracted > 0, (
                    f"No buying intent markers detected for {report.transcript_id}"
                )

    def test_engagement_trajectory_coverage(
        self, evaluation_reports: list[EvaluationReport],
    ):
        """Engagement trajectory should cover expected phases."""
        for report in evaluation_reports:
            trajectory = next(
                m for m in report.behavioral.signal_metrics
                if m.signal_name == "engagement_trajectory"
            )
            if trajectory.count_ground_truth > 0:
                assert trajectory.recall >= 0.5, (
                    f"Engagement trajectory recall too low for {report.transcript_id}"
                )


class TestPsychographicExtraction:
    """Evaluate Layer 3 extraction quality."""

    def test_mental_model_matches(self, evaluation_reports: list[EvaluationReport]):
        """Primary mental model should match ground truth across the corpus."""
        matches = sum(
            1 for r in evaluation_reports
            if next(
                m for m in r.psychographic.signal_metrics
                if m.signal_name == "mental_model"
            ).accuracy == 1.0
        )
        total = len(evaluation_reports)
        accuracy = matches / total if total else 0
        assert accuracy >= 0.5, f"Mental model accuracy: {accuracy:.0%} ({matches}/{total})"

    def test_persona_detected(self, evaluation_reports: list[EvaluationReport]):
        """At least one persona archetype should match ground truth."""
        for report in evaluation_reports:
            personas = next(
                m for m in report.psychographic.signal_metrics
                if m.signal_name == "persona_indicators"
            )
            if personas.count_ground_truth > 0:
                assert personas.recall > 0, (
                    f"No persona match for {report.transcript_id}"
                )

    def test_language_fingerprint_quality(
        self, evaluation_reports: list[EvaluationReport],
    ):
        """Language fingerprint should capture some distinctive vocabulary."""
        for report in evaluation_reports:
            fp = next(
                m for m in report.psychographic.signal_metrics
                if m.signal_name == "language_fingerprint"
            )
            if fp.count_ground_truth > 0:
                assert fp.recall >= 0.1, (
                    f"Language fingerprint recall too low for {report.transcript_id}"
                )


class TestMultimodalExtraction:
    """Evaluate multimodal divergence detection."""

    def test_divergence_detected_when_annotations_present(
        self, evaluation_reports: list[EvaluationReport],
    ):
        """If ground truth has divergences, extraction should find some."""
        for report in evaluation_reports:
            if report.multimodal is None:
                continue
            divergences = next(
                (m for m in report.multimodal.signal_metrics if m.signal_name == "divergences"),
                None,
            )
            if divergences and divergences.count_ground_truth > 0:
                assert divergences.count_extracted > 0, (
                    f"No divergences detected for {report.transcript_id}"
                )

    def test_no_multimodal_when_no_annotations(
        self,
        extracted_results: list[tuple[ExtractionResult, ExtractionResult, Transcript]],
    ):
        """If ground truth has no multimodal, extraction shouldn't produce it."""
        for result, gt, _ in extracted_results:
            if gt.multimodal is None:
                assert result.multimodal is None, (
                    f"Unexpected multimodal output for {result.transcript_id}"
                )
