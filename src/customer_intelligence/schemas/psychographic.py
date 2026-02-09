"""Layer 3: Psychographic signal schemas — mental models, persona indicators, language fingerprints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MentalModelType = Literal[
    "cost_reduction",
    "growth_enablement",
    "risk_mitigation",
    "efficiency",
]
ArchetypeType = Literal[
    "analytical_evaluator",
    "executive_champion",
    "reluctant_adopter",
]


class MentalModel(BaseModel):
    """The evaluation framework the buyer is using to make their decision."""

    primary: MentalModelType
    secondary: MentalModelType | None = None
    evidence: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class PersonaIndicator(BaseModel):
    """Signals suggesting which buyer archetype the prospect matches."""

    archetype: ArchetypeType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    reasoning: str


class LanguageFingerprint(BaseModel):
    """Distinctive vocabulary and framing patterns used by the prospect."""

    distinctive_vocabulary: list[str]
    metaphors: list[str]
    framing_patterns: list[str]


class PsychographicSignals(BaseModel):
    """Container for all Layer 3 psychographic signals."""

    mental_model: MentalModel
    persona_indicators: list[PersonaIndicator]
    language_fingerprint: LanguageFingerprint
