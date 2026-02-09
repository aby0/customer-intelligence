"""Schema validation tests — roundtrip serialization, required fields, constraints."""

import json

import pytest
from pydantic import ValidationError

from customer_intelligence.schemas.behavioral import (
    BehavioralSignals,
    BuyingIntentMarker,
    CompetitiveMention,
    EngagementTrajectoryPoint,
    Objection,
    ObjectionOutcome,
    ObjectionTriple,
    Resolution,
)
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.multimodal import (
    CompositeSentiment,
    DivergenceSignal,
    MultimodalSignals,
)
from customer_intelligence.schemas.psychographic import (
    LanguageFingerprint,
    MentalModel,
    PersonaIndicator,
    PsychographicSignals,
)
from customer_intelligence.schemas.summary import (
    ActionItem,
    KeyMoment,
    TranscriptSummary,
)
from customer_intelligence.schemas.surface import (
    AspectSentiment,
    KeyPhrase,
    NamedEntity,
    SurfaceSignals,
    TopicDetection,
)
from customer_intelligence.schemas.transcript import (
    AccountProfile,
    CallMetadata,
    ParalinguisticAnnotation,
    StakeholderProfile,
    Transcript,
    Utterance,
)


# --- Fixtures ---


def _make_surface() -> SurfaceSignals:
    return SurfaceSignals(
        aspects=[
            AspectSentiment(
                aspect="pricing",
                sentiment="negative",
                intensity=0.6,
                context="company size concern",
                source_utterance_indices=[3],
            )
        ],
        topics=[TopicDetection(name="pricing", timeline_position="mid", relevance=0.8)],
        entities=[NamedEntity(name="Acme", entity_type="company", mention_count=2)],
        key_phrases=[KeyPhrase(phrase="ROI", relevance=0.9)],
    )


def _make_behavioral() -> BehavioralSignals:
    return BehavioralSignals(
        objection_triples=[
            ObjectionTriple(
                objection=Objection(
                    type="pricing",
                    specific_language="The pricing feels steep for a company our size",
                    speaker_role="CFO",
                    conversation_stage="mid",
                    source_utterance_indices=[5],
                ),
                resolution=Resolution(
                    type="roi_argument",
                    specific_language="10x content output increase",
                    source_utterance_indices=[6],
                ),
                outcome=ObjectionOutcome(
                    resolved=True,
                    deal_progressed=True,
                    next_action="requested case study",
                ),
                confidence=0.85,
            )
        ],
        buying_intent_markers=[
            BuyingIntentMarker(
                type="timeline_question",
                evidence="When can we start implementation?",
                confidence=0.9,
                source_utterance_indices=[12],
            )
        ],
        competitive_mentions=[
            CompetitiveMention(
                competitor="CompetitorX",
                context="We looked at CompetitorX too",
                sentiment="neutral",
                comparison_type="alternative",
                source_utterance_indices=[8],
            )
        ],
        engagement_trajectory=[
            EngagementTrajectoryPoint(
                phase="early",
                participation_level="moderate",
                question_depth="surface",
                energy="medium",
            ),
            EngagementTrajectoryPoint(
                phase="late",
                participation_level="high",
                question_depth="deep",
                energy="high",
            ),
        ],
    )


def _make_psychographic() -> PsychographicSignals:
    return PsychographicSignals(
        mental_model=MentalModel(
            primary="cost_reduction",
            evidence=["reduce need for additional hires"],
            confidence=0.75,
            reasoning="Prospect focused on headcount costs throughout.",
        ),
        persona_indicators=[
            PersonaIndicator(
                archetype="analytical_evaluator",
                confidence=0.8,
                evidence=["Asked for ROI data", "Requested comparison matrix"],
                reasoning="Methodical evaluation with data requests.",
            )
        ],
        language_fingerprint=LanguageFingerprint(
            distinctive_vocabulary=["ROI", "headcount"],
            metaphors=["building a foundation"],
            framing_patterns=["in my experience"],
        ),
    )


def _make_multimodal() -> MultimodalSignals:
    return MultimodalSignals(
        divergences=[
            DivergenceSignal(
                utterance_index=5,
                type="text_positive_audio_negative",
                text_sentiment="positive",
                nonverbal_cues=["2.3s pause", "falling pitch", "low energy"],
                interpretation="likely hidden pricing concern",
                confidence=0.7,
            )
        ],
        composite_sentiments=[
            CompositeSentiment(
                utterance_index=5,
                original_text_polarity="positive",
                adjusted_polarity="neutral",
                confidence=0.45,
                note="verbal agreement contradicted by paralinguistic cues",
            )
        ],
    )


# --- Transcript tests ---


class TestTranscript:
    def test_minimal_transcript(self):
        t = Transcript(
            account=AccountProfile(
                company_name="Test",
                company_size="smb",
                industry="SaaS",
                deal_stage="discovery",
                deal_outcome="won",
                stakeholders=[
                    StakeholderProfile(
                        name="Jane", role="CEO", persona_type="executive_champion"
                    )
                ],
            ),
            call_metadata=CallMetadata(
                call_id="test_call1",
                call_date="2026-01-01",
                call_number=1,
                duration_minutes=30,
                participants=["rep", "prospect_ceo"],
            ),
            utterances=[
                Utterance(speaker="rep", text="Hello", turn_index=0),
                Utterance(speaker="prospect_ceo", text="Hi there", turn_index=1),
            ],
        )
        assert len(t.utterances) == 2

    def test_utterance_with_paralinguistic(self):
        u = Utterance(
            speaker="prospect_cfo",
            text="The pricing looks reasonable",
            turn_index=5,
            paralinguistic=ParalinguisticAnnotation(
                pause_before_sec=2.3,
                energy="low",
                pitch="falling",
                hesitation_markers=["um"],
                tone="hesitant",
                behaviors=["crossed_arms"],
            ),
        )
        assert u.paralinguistic is not None
        assert u.paralinguistic.energy == "low"

    def test_utterance_without_paralinguistic(self):
        u = Utterance(speaker="rep", text="Great question", turn_index=0)
        assert u.paralinguistic is None

    def test_invalid_company_size_rejected(self):
        with pytest.raises(ValidationError):
            AccountProfile(
                company_name="X",
                company_size="huge",  # type: ignore[arg-type]
                industry="SaaS",
                deal_stage="discovery",
                deal_outcome="won",
                stakeholders=[],
            )

    def test_call_number_must_be_positive(self):
        with pytest.raises(ValidationError):
            CallMetadata(
                call_id="x",
                call_date="2026-01-01",
                call_number=0,
                duration_minutes=30,
                participants=["rep"],
            )

    def test_roundtrip_serialization(self):
        t = Transcript(
            account=AccountProfile(
                company_name="Test",
                company_size="enterprise",
                industry="Tech",
                deal_stage="evaluation",
                deal_outcome="stalled",
                stakeholders=[],
            ),
            call_metadata=CallMetadata(
                call_id="rt_test",
                call_date="2026-01-15",
                call_number=1,
                duration_minutes=45,
                participants=["rep", "prospect"],
            ),
            utterances=[Utterance(speaker="rep", text="Hi", turn_index=0)],
        )
        json_str = t.model_dump_json()
        restored = Transcript.model_validate_json(json_str)
        assert restored == t


# --- Signal layer tests ---


class TestSurfaceSignals:
    def test_aspect_intensity_bounds(self):
        with pytest.raises(ValidationError):
            AspectSentiment(
                aspect="x", sentiment="positive", intensity=1.5,
                source_utterance_indices=[0],
            )

    def test_valid_surface_signals(self):
        s = _make_surface()
        assert len(s.aspects) == 1
        assert s.aspects[0].sentiment == "negative"


class TestBehavioralSignals:
    def test_objection_triple_with_no_resolution(self):
        triple = ObjectionTriple(
            objection=Objection(
                type="risk",
                specific_language="What if it breaks?",
                speaker_role="CISO",
                conversation_stage="late",
                source_utterance_indices=[10],
            ),
            resolution=None,
            outcome=ObjectionOutcome(resolved=False, deal_progressed=False),
            confidence=0.6,
        )
        assert triple.resolution is None
        assert not triple.outcome.resolved

    def test_valid_behavioral_signals(self):
        b = _make_behavioral()
        assert len(b.objection_triples) == 1
        assert b.objection_triples[0].outcome.resolved is True


class TestPsychographicSignals:
    def test_valid_psychographic_signals(self):
        p = _make_psychographic()
        assert p.mental_model.primary == "cost_reduction"

    def test_invalid_archetype_rejected(self):
        with pytest.raises(ValidationError):
            PersonaIndicator(
                archetype="unknown_type",  # type: ignore[arg-type]
                confidence=0.5,
                evidence=[],
                reasoning="test",
            )


class TestMultimodalSignals:
    def test_valid_multimodal_signals(self):
        m = _make_multimodal()
        assert len(m.divergences) == 1
        assert m.divergences[0].type == "text_positive_audio_negative"


# --- ExtractionResult composition test ---


class TestExtractionResult:
    def test_full_extraction_result(self):
        result = ExtractionResult(
            transcript_id="test_call1",
            extraction_timestamp="2026-02-07T00:00:00Z",
            surface=_make_surface(),
            behavioral=_make_behavioral(),
            psychographic=_make_psychographic(),
            multimodal=_make_multimodal(),
            overall_confidence=0.75,
            notes=["test note"],
        )
        assert result.multimodal is not None
        assert result.overall_confidence == 0.75

    def test_extraction_result_without_multimodal(self):
        result = ExtractionResult(
            transcript_id="test_call2",
            extraction_timestamp="2026-02-07T00:00:00Z",
            surface=_make_surface(),
            behavioral=_make_behavioral(),
            psychographic=_make_psychographic(),
            multimodal=None,
            overall_confidence=0.7,
        )
        assert result.multimodal is None
        assert result.notes == []

    def test_roundtrip_serialization(self):
        result = ExtractionResult(
            transcript_id="rt_test",
            extraction_timestamp="2026-02-07T00:00:00Z",
            surface=_make_surface(),
            behavioral=_make_behavioral(),
            psychographic=_make_psychographic(),
            multimodal=_make_multimodal(),
            overall_confidence=0.8,
        )
        json_str = result.model_dump_json()
        restored = ExtractionResult.model_validate_json(json_str)
        assert restored == result

    def test_json_schema_generation(self):
        """Verify the full JSON schema can be generated (used for LLM structured output)."""
        schema = ExtractionResult.model_json_schema()
        assert "properties" in schema
        assert "surface" in schema["properties"]
        assert "behavioral" in schema["properties"]
        assert "psychographic" in schema["properties"]


# --- Summary tests ---


class TestTranscriptSummary:
    def test_valid_summary(self):
        s = TranscriptSummary(
            executive_summary="This was a discovery call with CloudFirst Analytics.",
            key_moments=[
                KeyMoment(
                    moment_type="breakthrough",
                    description="Prospect acknowledged attribution gap",
                    significance="Validated the core pain point",
                    turn_indices=[5, 6],
                )
            ],
            action_items=[
                ActionItem(action="Send case study", owner="rep", criticality="high")
            ],
            prospect_priorities=["Attribution accuracy", "Time savings"],
            concerns_to_address=["Integration with existing tools"],
        )
        assert len(s.key_moments) == 1
        assert s.action_items[0].criticality == "high"

    def test_requires_at_least_one_key_moment(self):
        with pytest.raises(ValidationError):
            TranscriptSummary(
                executive_summary="Summary text.",
                key_moments=[],
                action_items=[],
                prospect_priorities=["Something"],
                concerns_to_address=[],
            )

    def test_requires_at_least_one_priority(self):
        with pytest.raises(ValidationError):
            TranscriptSummary(
                executive_summary="Summary text.",
                key_moments=[
                    KeyMoment(
                        moment_type="insight",
                        description="desc",
                        significance="sig",
                        turn_indices=[0],
                    )
                ],
                action_items=[],
                prospect_priorities=[],
                concerns_to_address=[],
            )

    def test_invalid_moment_type_rejected(self):
        with pytest.raises(ValidationError):
            KeyMoment(
                moment_type="celebration",  # type: ignore[arg-type]
                description="desc",
                significance="sig",
                turn_indices=[0],
            )

    def test_invalid_criticality_rejected(self):
        with pytest.raises(ValidationError):
            ActionItem(
                action="do something",
                owner="rep",
                criticality="critical",  # type: ignore[arg-type]
            )

    def test_roundtrip_serialization(self):
        s = TranscriptSummary(
            executive_summary="Summary.",
            key_moments=[
                KeyMoment(
                    moment_type="commitment",
                    description="Agreed to next call",
                    significance="Deal moving forward",
                    turn_indices=[20],
                )
            ],
            action_items=[],
            prospect_priorities=["Speed"],
            concerns_to_address=["Budget approval"],
        )
        json_str = s.model_dump_json()
        restored = TranscriptSummary.model_validate_json(json_str)
        assert restored == s
