"""Layer 1: Surface signal schemas — aspect sentiment, topics, entities, key phrases."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SentimentPolarity = Literal["positive", "negative", "neutral", "mixed"]
EntityType = Literal["person", "company", "product", "competitor"]


class AspectSentiment(BaseModel):
    """Sentiment about a specific aspect within an utterance or across utterances."""

    aspect: str
    sentiment: SentimentPolarity
    intensity: float = Field(ge=0.0, le=1.0)
    context: str | None = None
    source_utterance_indices: list[int]


class TopicDetection(BaseModel):
    """A topic discussed during the call with timeline positioning."""

    name: str
    timeline_position: Literal["early", "mid", "late"]
    relevance: float = Field(ge=0.0, le=1.0)


class NamedEntity(BaseModel):
    """A person, company, product, or competitor mentioned in the call."""

    name: str
    entity_type: EntityType
    role: str | None = None
    mention_count: int = Field(ge=1)


class KeyPhrase(BaseModel):
    """An important term or concept from the conversation."""

    phrase: str
    relevance: float = Field(ge=0.0, le=1.0)
    context: str | None = None


class SurfaceSignals(BaseModel):
    """Container for all Layer 1 surface signals."""

    aspects: list[AspectSentiment]
    topics: list[TopicDetection]
    entities: list[NamedEntity]
    key_phrases: list[KeyPhrase]
