"""Module 1: Signal extraction orchestrator.

Takes a Transcript, runs extraction prompts for each layer,
and returns a structured ExtractionResult.
"""

from __future__ import annotations

import json
import re
import sys
import types
import typing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, get_args, get_origin

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

from customer_intelligence.schemas.behavioral import BehavioralSignals
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.multimodal import MultimodalSignals
from customer_intelligence.schemas.psychographic import PsychographicSignals
from customer_intelligence.schemas.summary import TranscriptSummary
from customer_intelligence.schemas.surface import SurfaceSignals
from customer_intelligence.schemas.transcript import Transcript

from .prompts import (
    BEHAVIORAL_EXTRACTION_PROMPT,
    MULTIMODAL_DIVERGENCE_PROMPT,
    PSYCHOGRAPHIC_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
    SURFACE_EXTRACTION_PROMPT,
)

load_dotenv()

MODEL = "claude-opus-4-6"


def _format_transcript(transcript: Transcript) -> str:
    """Format a transcript into a readable string for prompt injection."""
    lines = []
    for u in transcript.utterances:
        para = ""
        if u.paralinguistic:
            parts = []
            if u.paralinguistic.pause_before_sec:
                parts.append(f"{u.paralinguistic.pause_before_sec}s pause")
            if u.paralinguistic.energy:
                parts.append(f"energy: {u.paralinguistic.energy.upper()}")
            if u.paralinguistic.pitch:
                parts.append(f"pitch: {u.paralinguistic.pitch.upper()}")
            if u.paralinguistic.hesitation_markers:
                parts.append(f"hesitation: {', '.join(u.paralinguistic.hesitation_markers)}")
            if u.paralinguistic.tone:
                parts.append(f"tone: {u.paralinguistic.tone}")
            if u.paralinguistic.behaviors:
                parts.append(f"behaviors: {', '.join(u.paralinguistic.behaviors)}")
            if parts:
                para = f" [{'; '.join(parts)}]"

        lines.append(f"[{u.turn_index}] {u.speaker}:{para} {u.text}")
    return "\n".join(lines)


def _has_paralinguistic(transcript: Transcript) -> bool:
    """Check if any utterance has paralinguistic annotations."""
    return any(u.paralinguistic is not None for u in transcript.utterances)


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from an LLM response, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _repair_json(text)
        return json.loads(repaired)


def _repair_json(text: str) -> str:
    """Repair common LLM JSON issues like unquoted annotations after string values."""
    # Fix: "value" - commentary  →  "value - commentary"
    text = re.sub(
        r'"([^"]*?)"\s+-\s+([^"\n,\]\}]+)\s*(?=[,\]\}])',
        lambda m: '"' + m.group(1) + ' - ' + m.group(2).strip() + '"',
        text,
    )
    # Fix trailing commas before ] or }
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    return text


def _coerce_to_schema(data: object, model_cls: type[BaseModel]) -> object:
    """Recursively coerce raw LLM data to match Pydantic model constraints.

    For Literal fields, maps unrecognized values to 'other' if available,
    otherwise picks the first valid value.
    """
    if not isinstance(data, dict):
        return data

    result = dict(data)
    fields = model_cls.model_fields

    # Fill missing required Literal fields with their first valid value
    for field_name, field_info in fields.items():
        if field_name not in result and field_info.is_required():
            annotation = field_info.annotation
            origin = get_origin(annotation)
            if origin is Literal:
                result[field_name] = get_args(annotation)[0]

    for key, value in list(result.items()):
        field_info = fields.get(key)
        if field_info is None:
            continue

        annotation = field_info.annotation

        # Unwrap Optional (X | None) via union types
        origin = get_origin(annotation)
        inner = annotation
        if origin is typing.Union or isinstance(annotation, types.UnionType):
            args = get_args(annotation)
            non_none = [a for a in args if a is not type(None)]
            if non_none:
                inner = non_none[0]

        inner_origin = get_origin(inner)
        inner_args = get_args(inner)

        # Handle Literal fields
        if inner_origin is Literal:
            valid_values = set(inner_args)
            if isinstance(value, str) and value not in valid_values:
                result[key] = "other" if "other" in valid_values else inner_args[0]
            else:
                result[key] = value

        # Handle list[SubModel] fields
        elif inner_origin is list and inner_args:
            item_type = inner_args[0]
            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                result[key] = [_coerce_to_schema(item, item_type) for item in value] if isinstance(value, list) else value
            else:
                result[key] = value

        # Handle nested BaseModel fields
        elif isinstance(inner, type) and issubclass(inner, BaseModel):
            result[key] = _coerce_to_schema(value, inner) if isinstance(value, dict) else value

        else:
            result[key] = value

    return result


def _extract_layer(
    client: anthropic.Anthropic,
    prompt_template: str,
    transcript_text: str,
) -> dict:
    """Call Claude to extract a single signal layer, retrying on malformed JSON."""
    prompt = prompt_template.format(transcript=transcript_text)
    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=messages,
    )
    raw = response.content[0].text
    try:
        return _parse_json_response(raw)
    except json.JSONDecodeError as e:
        # Ask the LLM to fix its own malformed JSON
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                f"Your response is not valid JSON. Error: {e}. "
                "Please return ONLY the corrected valid JSON with no commentary."
            ),
        })
        retry = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=messages,
        )
        return _parse_json_response(retry.content[0].text)


def extract(
    transcript: Transcript,
    client: anthropic.Anthropic | None = None,
) -> ExtractionResult:
    """Extract all signal layers from a transcript.

    Runs surface, behavioral, and psychographic extraction.
    Runs multimodal divergence detection only if paralinguistic annotations are present.
    Flags low-confidence Layer 3 for short transcripts (<10 turns).
    """
    if client is None:
        client = anthropic.Anthropic()

    transcript_text = _format_transcript(transcript)
    notes: list[str] = []

    # Layer 1: Surface signals
    surface_data = _extract_layer(client, SURFACE_EXTRACTION_PROMPT, transcript_text)
    surface = SurfaceSignals.model_validate(_coerce_to_schema(surface_data, SurfaceSignals))

    # Layer 2: Behavioral signals
    behavioral_data = _extract_layer(client, BEHAVIORAL_EXTRACTION_PROMPT, transcript_text)
    behavioral = BehavioralSignals.model_validate(_coerce_to_schema(behavioral_data, BehavioralSignals))

    # Layer 3: Psychographic signals
    psychographic_data = _extract_layer(client, PSYCHOGRAPHIC_EXTRACTION_PROMPT, transcript_text)
    psychographic = PsychographicSignals.model_validate(_coerce_to_schema(psychographic_data, PsychographicSignals))

    if len(transcript.utterances) < 10:
        notes.append(
            "Short transcript (<10 turns) — Layer 3 psychographic signals are low confidence"
        )

    # Multimodal: only if paralinguistic annotations present
    multimodal: MultimodalSignals | None = None
    if _has_paralinguistic(transcript):
        multimodal_data = _extract_layer(
            client, MULTIMODAL_DIVERGENCE_PROMPT, transcript_text
        )
        multimodal = MultimodalSignals.model_validate(_coerce_to_schema(multimodal_data, MultimodalSignals))
    else:
        notes.append("No paralinguistic annotations — multimodal extraction skipped")

    # Compute overall confidence as average of layer-level signals
    confidences = []
    for triple in behavioral.objection_triples:
        confidences.append(triple.confidence)
    for marker in behavioral.buying_intent_markers:
        confidences.append(marker.confidence)
    confidences.append(psychographic.mental_model.confidence)
    for indicator in psychographic.persona_indicators:
        confidences.append(indicator.confidence)
    overall = sum(confidences) / len(confidences) if confidences else 0.5

    return ExtractionResult(
        transcript_id=transcript.call_metadata.call_id,
        extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        surface=surface,
        behavioral=behavioral,
        psychographic=psychographic,
        multimodal=multimodal,
        overall_confidence=round(overall, 2),
        notes=notes,
    )


def extract_summary(
    transcript: Transcript,
    client: anthropic.Anthropic | None = None,
) -> TranscriptSummary:
    """Extract a human-readable summary of a sales call transcript."""
    if client is None:
        client = anthropic.Anthropic()

    transcript_text = _format_transcript(transcript)
    summary_data = _extract_layer(client, SUMMARY_PROMPT, transcript_text)
    return TranscriptSummary.model_validate(
        _coerce_to_schema(summary_data, TranscriptSummary)
    )


EXTRACTIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "extractions"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m customer_intelligence.extraction.extractor <transcript.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    transcript = Transcript.model_validate_json(path.read_text())
    result = extract(transcript)

    EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXTRACTIONS_DIR / f"{result.transcript_id}.json"
    out_path.write_text(result.model_dump_json(indent=2))
    print(f"Saved extraction to {out_path}")
