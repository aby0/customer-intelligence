"""Multimodal divergence detection schemas — text-audio divergence and composite sentiment."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .surface import SentimentPolarity

DivergenceType = Literal[
    "text_positive_audio_negative",
    "text_negative_audio_positive",
    "text_neutral_audio_negative",
    "text_neutral_audio_positive",
]


class DivergenceSignal(BaseModel):
    """A detected contradiction between text sentiment and non-verbal cues."""

    utterance_index: int
    type: DivergenceType
    text_sentiment: SentimentPolarity
    nonverbal_cues: list[str]
    interpretation: str
    confidence: float = Field(ge=0.0, le=1.0)


class CompositeSentiment(BaseModel):
    """Sentiment score adjusted by multimodal signal fusion."""

    utterance_index: int
    original_text_polarity: SentimentPolarity
    adjusted_polarity: SentimentPolarity
    confidence: float = Field(ge=0.0, le=1.0)
    note: str | None = None


class MultimodalSignals(BaseModel):
    """Container for all multimodal divergence signals."""

    divergences: list[DivergenceSignal]
    composite_sentiments: list[CompositeSentiment]
