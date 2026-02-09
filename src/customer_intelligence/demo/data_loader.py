"""Data loading utilities for the Streamlit demo app."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.summary import TranscriptSummary
from customer_intelligence.schemas.transcript import Transcript

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
EXTRACTIONS_DIR = DATA_DIR / "extractions"
SUMMARIES_DIR = DATA_DIR / "summaries"
DOCS_DIR = PROJECT_ROOT / "docs"


@st.cache_data
def _load_transcripts_raw() -> dict[str, str]:
    """Load raw JSON strings for transcripts (cacheable)."""
    return {p.stem: p.read_text() for p in sorted(TRANSCRIPTS_DIR.glob("*.json"))}


def load_transcripts() -> dict[str, Transcript]:
    raw = _load_transcripts_raw()
    return {k: Transcript.model_validate_json(v) for k, v in raw.items()}


@st.cache_data
def _load_extractions_raw() -> dict[str, str]:
    """Load raw JSON strings for extractions (ground truth first, then pipeline)."""
    data: dict[str, str] = {}
    for p in sorted(GROUND_TRUTH_DIR.glob("*.json")):
        data[p.stem] = p.read_text()
    for p in sorted(EXTRACTIONS_DIR.glob("*.json")):
        data[p.stem] = p.read_text()
    return data


def load_extractions() -> dict[str, ExtractionResult]:
    raw = _load_extractions_raw()
    return {k: ExtractionResult.model_validate_json(v) for k, v in raw.items()}


@st.cache_data
def _load_summaries_raw() -> dict[str, str]:
    """Load raw JSON strings for summaries (cacheable)."""
    if not SUMMARIES_DIR.exists():
        return {}
    return {p.stem: p.read_text() for p in sorted(SUMMARIES_DIR.glob("*.json"))}


def load_summaries() -> dict[str, TranscriptSummary]:
    raw = _load_summaries_raw()
    return {k: TranscriptSummary.model_validate_json(v) for k, v in raw.items()}


@st.cache_data(ttl=10)
def load_docs() -> dict[str, str]:
    """Auto-discover and load all .md files from docs/ directory."""
    if not DOCS_DIR.exists():
        return {}
    docs: dict[str, str] = {}
    for p in sorted(DOCS_DIR.glob("*.md")):
        title = p.stem.replace("-", " ").replace("_", " ").title()
        docs[title] = p.read_text()
    return docs


def get_display_label(transcript: Transcript) -> str:
    """Format a readable dropdown label for a transcript."""
    a = transcript.account
    size = a.company_size.replace("_", "-")
    return f"{a.company_name} ({size}, {a.deal_outcome}) - Call {transcript.call_metadata.call_number}"


def has_paralinguistic(transcript: Transcript) -> bool:
    return any(u.paralinguistic is not None for u in transcript.utterances)
