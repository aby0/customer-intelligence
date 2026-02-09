"""Top-level extraction result that composes all signal layers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .behavioral import BehavioralSignals
from .multimodal import MultimodalSignals
from .psychographic import PsychographicSignals
from .surface import SurfaceSignals


class ExtractionResult(BaseModel):
    """Complete signal extraction output for a single sales call transcript."""

    transcript_id: str
    extraction_timestamp: str
    surface: SurfaceSignals
    behavioral: BehavioralSignals
    psychographic: PsychographicSignals
    multimodal: MultimodalSignals | None = None
    overall_confidence: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)
