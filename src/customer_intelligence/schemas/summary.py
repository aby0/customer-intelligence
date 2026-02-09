"""Transcript summary schemas — executive summary, key moments, action items."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class KeyMoment(BaseModel):
    """A critical conversation turning point."""

    moment_type: Literal["breakthrough", "objection", "commitment", "risk", "insight"]
    description: str
    significance: str
    turn_indices: list[int]


class ActionItem(BaseModel):
    """A follow-up action identified in the call."""

    action: str
    owner: str
    criticality: Literal["high", "medium", "low"]


class TranscriptSummary(BaseModel):
    """Human-readable summary of a sales call."""

    executive_summary: str
    key_moments: list[KeyMoment] = Field(min_length=1)
    action_items: list[ActionItem]
    prospect_priorities: list[str] = Field(min_length=1)
    concerns_to_address: list[str]
