"""Synthetic data corpus coverage tests.

Validates that the generated corpus meets the spec requirements.
Runs against saved data files — no LLM calls.
"""

import json
from pathlib import Path

import pytest

from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.transcript import Transcript
from customer_intelligence.synthetic.profiles import PROFILES

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"


def _load_transcripts() -> list[Transcript]:
    """Load all generated transcripts."""
    files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    return [Transcript.model_validate_json(f.read_text()) for f in files]


def _load_ground_truths() -> list[ExtractionResult]:
    """Load all ground truth files."""
    files = sorted(GROUND_TRUTH_DIR.glob("*.json"))
    return [ExtractionResult.model_validate_json(f.read_text()) for f in files]


@pytest.fixture(scope="module")
def transcripts() -> list[Transcript]:
    files = list(TRANSCRIPTS_DIR.glob("*.json"))
    if not files:
        pytest.skip("No synthetic transcripts generated yet — run generator first")
    return _load_transcripts()


@pytest.fixture(scope="module")
def ground_truths() -> list[ExtractionResult]:
    files = list(GROUND_TRUTH_DIR.glob("*.json"))
    if not files:
        pytest.skip("No ground truth files generated yet — run generator first")
    return _load_ground_truths()


class TestCorpusCoverage:
    """Verify the corpus meets spec acceptance criteria."""

    def test_at_least_5_accounts(self, transcripts: list[Transcript]):
        accounts = {t.account.company_name for t in transcripts}
        assert len(accounts) >= 5

    def test_at_least_3_deal_outcomes(self, transcripts: list[Transcript]):
        outcomes = {t.account.deal_outcome for t in transcripts}
        assert outcomes >= {"won", "lost", "stalled"}

    def test_at_least_3_persona_types(self, transcripts: list[Transcript]):
        personas = set()
        for t in transcripts:
            for s in t.account.stakeholders:
                personas.add(s.persona_type)
        assert personas >= {"analytical_evaluator", "executive_champion", "reluctant_adopter"}

    def test_at_least_4_deal_stages(self, transcripts: list[Transcript]):
        stages = {t.account.deal_stage for t in transcripts}
        assert len(stages) >= 4

    def test_multi_call_threads_exist(self, transcripts: list[Transcript]):
        """At least 2 accounts have multiple calls."""
        from collections import Counter
        account_call_counts = Counter(t.account.company_name for t in transcripts)
        multi_call_accounts = [a for a, c in account_call_counts.items() if c >= 2]
        assert len(multi_call_accounts) >= 2


class TestTranscriptQuality:
    """Verify individual transcript properties."""

    def test_speaker_labels_present(self, transcripts: list[Transcript]):
        for t in transcripts:
            speakers = {u.speaker for u in t.utterances}
            assert "rep" in speakers, f"{t.call_metadata.call_id} missing 'rep' speaker"

    def test_turn_indices_sequential(self, transcripts: list[Transcript]):
        for t in transcripts:
            indices = [u.turn_index for u in t.utterances]
            assert indices == sorted(indices), (
                f"{t.call_metadata.call_id} has non-sequential turn indices"
            )

    def test_transcript_length_variety(self, transcripts: list[Transcript]):
        lengths = [len(t.utterances) for t in transcripts]
        assert min(lengths) <= 20, "No short transcripts in corpus"
        assert max(lengths) >= 35, "No long transcripts in corpus"


class TestParalinguisticAnnotations:
    """Verify paralinguistic annotation coverage."""

    def test_some_transcripts_have_annotations(self, transcripts: list[Transcript]):
        annotated = [
            t for t in transcripts
            if any(u.paralinguistic is not None for u in t.utterances)
        ]
        assert len(annotated) >= 3

    def test_some_transcripts_lack_annotations(self, transcripts: list[Transcript]):
        unannotated = [
            t for t in transcripts
            if all(u.paralinguistic is None for u in t.utterances)
        ]
        assert len(unannotated) >= 2


class TestGroundTruth:
    """Verify ground truth files exist and are valid."""

    def test_each_transcript_has_ground_truth(
        self, transcripts: list[Transcript], ground_truths: list[ExtractionResult]
    ):
        transcript_ids = {t.call_metadata.call_id for t in transcripts}
        gt_ids = {gt.transcript_id for gt in ground_truths}
        assert transcript_ids == gt_ids

    def test_ground_truth_has_all_layers(self, ground_truths: list[ExtractionResult]):
        for gt in ground_truths:
            assert gt.surface is not None
            assert gt.behavioral is not None
            assert gt.psychographic is not None

    def test_at_least_3_objection_types_in_corpus(
        self, ground_truths: list[ExtractionResult]
    ):
        objection_types = set()
        for gt in ground_truths:
            for triple in gt.behavioral.objection_triples:
                objection_types.add(triple.objection.type)
        assert len(objection_types) >= 3
