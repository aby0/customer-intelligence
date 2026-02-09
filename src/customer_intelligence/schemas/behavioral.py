"""Layer 2: Behavioral signal schemas — objection triples, buying intent, competitive mentions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .surface import SentimentPolarity

ObjectionType = Literal[
    "pricing",
    "implementation",
    "competition",
    "timeline",
    "risk",
    "authority",
    "need",
    "other",
]
ResolutionType = Literal[
    "roi_argument",
    "social_proof",
    "discount",
    "phased_rollout",
    "technical_demo",
    "risk_mitigation",
    "other",
]
IntentMarkerType = Literal[
    "timeline_question",
    "stakeholder_introduction",
    "if_to_when_shift",
    "implementation_detail",
    "budget_confirmation",
    "next_steps_request",
    "other",
]


class Objection(BaseModel):
    """A concern or pushback raised by the prospect."""

    type: ObjectionType
    specific_language: str
    speaker_role: str
    conversation_stage: Literal["early", "mid", "late"]
    source_utterance_indices: list[int]


class Resolution(BaseModel):
    """A sales rep's attempt to address an objection."""

    type: ResolutionType
    specific_language: str
    speaker_role: str = "rep"
    source_utterance_indices: list[int]


class ObjectionOutcome(BaseModel):
    """The result of an objection-resolution exchange."""

    resolved: bool
    deal_progressed: bool
    next_action: str | None = None


class ObjectionTriple(BaseModel):
    """An objection -> resolution -> outcome sequence."""

    objection: Objection
    resolution: Resolution | None = None
    outcome: ObjectionOutcome
    confidence: float = Field(ge=0.0, le=1.0)


class BuyingIntentMarker(BaseModel):
    """A linguistic cue that correlates with deal progression."""

    type: IntentMarkerType
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_utterance_indices: list[int]


class CompetitiveMention(BaseModel):
    """A reference to a competitor during the call."""

    competitor: str
    context: str
    sentiment: SentimentPolarity
    comparison_type: str | None = None
    source_utterance_indices: list[int]


class EngagementTrajectoryPoint(BaseModel):
    """Prospect engagement level at a phase of the conversation."""

    phase: Literal["early", "mid", "late"]
    participation_level: Literal["low", "moderate", "high"]
    question_depth: Literal["surface", "moderate", "deep"]
    energy: Literal["low", "medium", "high"]
    notes: str | None = None


class BehavioralSignals(BaseModel):
    """Container for all Layer 2 behavioral signals."""

    objection_triples: list[ObjectionTriple]
    buying_intent_markers: list[BuyingIntentMarker]
    competitive_mentions: list[CompetitiveMention]
    engagement_trajectory: list[EngagementTrajectoryPoint]
