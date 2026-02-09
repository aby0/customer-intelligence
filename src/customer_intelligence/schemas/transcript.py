"""Input schemas: sales call transcripts with optional paralinguistic annotations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EnergyLevel = Literal["low", "medium", "high"]
PitchDirection = Literal["rising", "falling", "flat"]
CompanySize = Literal["startup", "smb", "mid_market", "enterprise"]
DealStage = Literal["discovery", "evaluation", "negotiation", "close"]
DealOutcome = Literal["won", "lost", "stalled"]
PersonaType = Literal["analytical_evaluator", "executive_champion", "reluctant_adopter"]


class ParalinguisticAnnotation(BaseModel):
    """Simulated audio/video signals embedded in transcript annotations."""

    pause_before_sec: float | None = None
    energy: EnergyLevel | None = None
    pitch: PitchDirection | None = None
    hesitation_markers: list[str] = Field(default_factory=list)
    tone: str | None = None
    behaviors: list[str] = Field(default_factory=list)


class Utterance(BaseModel):
    """A single speaker turn in a sales call transcript."""

    speaker: str
    text: str
    turn_index: int
    paralinguistic: ParalinguisticAnnotation | None = None


class StakeholderProfile(BaseModel):
    """A participant in the buying process."""

    name: str
    role: str
    persona_type: PersonaType


class AccountProfile(BaseModel):
    """Company and deal context for a sales engagement."""

    company_name: str
    company_size: CompanySize
    industry: str
    deal_stage: DealStage
    deal_outcome: DealOutcome
    stakeholders: list[StakeholderProfile]


class CallMetadata(BaseModel):
    """Metadata for a single sales call recording."""

    call_id: str
    call_date: str
    call_number: int = Field(ge=1)
    duration_minutes: int
    participants: list[str]


class Transcript(BaseModel):
    """A complete sales call transcript with account context."""

    account: AccountProfile
    call_metadata: CallMetadata
    utterances: list[Utterance]
