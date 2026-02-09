"""LLM-powered synthetic transcript and ground truth generation.

Generates realistic sales call transcripts from account profiles,
then generates companion ground truth extraction annotations.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.transcript import (
    CallMetadata,
    Transcript,
)

from .profiles import PROFILES, GenerationProfile

load_dotenv()


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from an LLM response, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        # Strip ```json or ``` fences
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end])
    # Extract JSON object even if surrounded by extra text
    brace_start = text.find("{")
    if brace_start == -1:
        raise ValueError(f"No JSON object found in response: {text[:200]}")
    text = text[brace_start:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt repair: trailing commas and single-line comments
        repaired = re.sub(r",\s*([}\]])", r"\1", text)
        # Strip inline annotations the LLM adds after string values:
        #   "value" (parenthetical note)   →  "value"
        #   "value" - dash annotation"     →  "value"
        repaired = re.sub(
            r'("(?:[^"\\]|\\.)*")\s*\([^)]*\)"?', r"\1", repaired
        )
        repaired = re.sub(
            r'("(?:[^"\\]|\\.)*")\s+-\s+.*?"(?=\s*[,\]\}])', r"\1", repaired
        )
        return json.loads(repaired)

_MAX_RETRIES = 3


def _llm_generate_json(
    client: anthropic.Anthropic,
    prompt: str,
    max_tokens: int = 16384,
) -> dict:
    """Call the LLM, parse the JSON response, and retry on failure."""
    last_error = None
    for attempt in range(_MAX_RETRIES):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "{"},
            ],
        )
        raw = "{" + response.content[0].text

        if response.stop_reason == "end_turn":
            try:
                return _parse_json_response(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                # Dump failing response for debugging
                debug_path = DATA_DIR / f"_debug_response_{attempt}.txt"
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                debug_path.write_text(raw)
                print(f"    Retry {attempt + 1}/{_MAX_RETRIES}: JSON parse error — {exc}")
        else:
            last_error = ValueError(
                f"Response truncated (stop_reason={response.stop_reason})"
            )
            print(f"    Retry {attempt + 1}/{_MAX_RETRIES}: response truncated")

        time.sleep(1)

    raise RuntimeError(
        f"Failed to get valid JSON after {_MAX_RETRIES} attempts: {last_error}"
    )


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"


def _build_transcript_prompt(profile: GenerationProfile, call_number: int) -> str:
    """Build a prompt that generates a realistic sales call transcript."""
    account = profile.account
    stakeholder_desc = "\n".join(
        f"  - {s.name} ({s.role}): persona type = {s.persona_type}"
        for s in account.stakeholders
    )

    paralinguistic_instructions = ""
    if profile.include_paralinguistic:
        paralinguistic_instructions = """
PARALINGUISTIC ANNOTATIONS:
Include inline annotations for audio/video signals in the transcript. For EACH utterance
that has notable non-verbal signals, add a "paralinguistic" object with these fields:
- pause_before_sec: seconds of silence before the utterance (null if normal)
- energy: "low", "medium", or "high"
- pitch: "rising", "falling", or "flat"
- hesitation_markers: list of filler words like ["um", "uh"] (empty list if none)
- tone: free-text descriptor like "hesitant", "confident", "enthusiastic", "guarded"
- behaviors: list of visual cues like ["lean_forward", "note_taking", "crossed_arms"]

IMPORTANT: Create at least 2 text-audio DIVERGENCE scenarios where the text sentiment
contradicts the non-verbal cues (e.g., positive words + low energy + hesitation = hidden concern).
Not every utterance needs paralinguistic annotations — about 40-60% should have them,
focusing on emotionally significant moments.
"""

    multi_call_context = ""
    if profile.call_count > 1 and call_number > 1:
        multi_call_context = f"""
This is call {call_number} of {profile.call_count} with this account.
Reference the previous call naturally (e.g., "As we discussed last week...").
Show evolution: objections from earlier calls may be addressed, new concerns may emerge,
engagement level should shift based on what happened between calls.
"""

    stage_desc = account.deal_stage
    if profile.call_count > 1:
        stages = {1: "evaluation", 2: "close"} if account.deal_outcome == "won" else {1: "evaluation", 2: "evaluation"}
        stage_desc = stages.get(call_number, account.deal_stage)

    return f"""Generate a realistic B2B sales call transcript as a JSON object.

ACCOUNT CONTEXT:
- Company: {account.company_name} ({account.company_size}, {account.industry})
- Deal stage: {stage_desc}
- Deal outcome (not visible in transcript): {account.deal_outcome}
- Stakeholders:
{stakeholder_desc}

GENERATION INSTRUCTIONS:
{profile.generation_notes}
{multi_call_context}
TRANSCRIPT REQUIREMENTS:
- Target approximately {profile.target_turn_count} turns
- Speaker labels must use these identifiers: "rep" for the sales representative,
  and "prospect_<role_snake_case>" for each prospect (e.g., "prospect_cfo", "prospect_vp_marketing")
- Include realistic conversational flow — not rigid Q&A
- Embed these objection types naturally: {profile.objection_types}
- {"Include competitive mentions of: " + ", ".join(profile.competitive_mentions) if profile.competitive_mentions else "No explicit competitor mentions needed"}
- Each utterance needs: speaker (string), text (string), turn_index (integer starting at 0)
{paralinguistic_instructions}
Return ONLY a valid JSON object with this structure:
{{
  "utterances": [
    {{
      "speaker": "rep",
      "text": "...",
      "turn_index": 0,
      "paralinguistic": null
    }},
    ...
  ]
}}

Do not include any text outside the JSON object."""


def _build_ground_truth_prompt(transcript_json: str, profile: GenerationProfile) -> str:
    """Build a prompt that generates ground truth extraction annotations."""
    return f"""You are annotating a sales call transcript with ground truth signal extractions.
This will be used to evaluate an automated extraction pipeline.

TRANSCRIPT:
{transcript_json}

ACCOUNT CONTEXT (known but not in transcript):
- Company: {profile.account.company_name} ({profile.account.company_size})
- Deal outcome: {profile.account.deal_outcome}
- Stakeholder personas: {", ".join(f"{s.name} = {s.persona_type}" for s in profile.account.stakeholders)}

Extract ALL signals across three layers, plus multimodal if paralinguistic annotations are present.

Return ONLY a valid JSON object matching this schema:

{{
  "surface": {{
    "aspects": [
      {{"aspect": "string", "sentiment": "positive|negative|neutral|mixed",
        "intensity": 0.0-1.0, "context": "string or null",
        "source_utterance_indices": [int]}}
    ],
    "topics": [
      {{"name": "string", "timeline_position": "early|mid|late", "relevance": 0.0-1.0}}
    ],
    "entities": [
      {{"name": "string", "entity_type": "person|company|product|competitor",
        "role": "string or null", "mention_count": int}}
    ],
    "key_phrases": [
      {{"phrase": "string", "relevance": 0.0-1.0, "context": "string or null"}}
    ]
  }},
  "behavioral": {{
    "objection_triples": [
      {{
        "objection": {{
          "type": "pricing|implementation|competition|timeline|risk|authority|need|other",
          "specific_language": "direct quote from transcript",
          "speaker_role": "string",
          "conversation_stage": "early|mid|late",
          "source_utterance_indices": [int]
        }},
        "resolution": {{
          "type": "roi_argument|social_proof|discount|phased_rollout|technical_demo|risk_mitigation|other",
          "specific_language": "direct quote",
          "speaker_role": "rep",
          "source_utterance_indices": [int]
        }} or null,
        "outcome": {{
          "resolved": bool,
          "deal_progressed": bool,
          "next_action": "string or null"
        }},
        "confidence": 0.0-1.0
      }}
    ],
    "buying_intent_markers": [
      {{"type": "timeline_question|stakeholder_introduction|if_to_when_shift|implementation_detail|budget_confirmation|next_steps_request|other",
        "evidence": "specific language", "confidence": 0.0-1.0,
        "source_utterance_indices": [int]}}
    ],
    "competitive_mentions": [
      {{"competitor": "string", "context": "string",
        "sentiment": "positive|negative|neutral|mixed",
        "comparison_type": "string or null", "source_utterance_indices": [int]}}
    ],
    "engagement_trajectory": [
      {{"phase": "early|mid|late",
        "participation_level": "low|moderate|high",
        "question_depth": "surface|moderate|deep",
        "energy": "low|medium|high", "notes": "string or null"}}
    ]
  }},
  "psychographic": {{
    "mental_model": {{
      "primary": "cost_reduction|growth_enablement|risk_mitigation|efficiency",
      "secondary": "same options or null",
      "evidence": ["quote or observation"],
      "confidence": 0.0-1.0,
      "reasoning": "chain-of-thought explanation"
    }},
    "persona_indicators": [
      {{"archetype": "analytical_evaluator|executive_champion|reluctant_adopter",
        "confidence": 0.0-1.0, "evidence": ["..."], "reasoning": "..."}}
    ],
    "language_fingerprint": {{
      "distinctive_vocabulary": ["terms the prospect uses"],
      "metaphors": ["..."],
      "framing_patterns": ["..."]
    }}
  }},
  "multimodal": {"null if no paralinguistic annotations are present, otherwise:" if not profile.include_paralinguistic else ""}
  {{
    "divergences": [
      {{"utterance_index": int,
        "type": "text_positive_audio_negative|text_negative_audio_positive|text_neutral_audio_negative|text_neutral_audio_positive",
        "text_sentiment": "positive|negative|neutral|mixed",
        "nonverbal_cues": ["2.3s pause", "falling pitch"],
        "interpretation": "likely hidden pricing concern",
        "confidence": 0.0-1.0}}
    ],
    "composite_sentiments": [
      {{"utterance_index": int,
        "original_text_polarity": "positive|negative|neutral|mixed",
        "adjusted_polarity": "positive|negative|neutral|mixed",
        "confidence": 0.0-1.0, "note": "string or null"}}
    ]
  }}
}}

Be thorough — extract every signal present in the transcript.
Do not include any text outside the JSON object."""


def _call_id(profile: GenerationProfile, call_number: int) -> str:
    slug = profile.account.company_name.lower().replace(" ", "_")
    return f"{slug}_call{call_number}"


def generate_transcript(
    client: anthropic.Anthropic,
    profile: GenerationProfile,
    call_number: int = 1,
) -> Transcript:
    """Generate a single synthetic transcript from a profile."""
    prompt = _build_transcript_prompt(profile, call_number)
    data = _llm_generate_json(client, prompt, max_tokens=8192)
    call_id = _call_id(profile, call_number)

    return Transcript(
        account=profile.account,
        call_metadata=CallMetadata(
            call_id=call_id,
            call_date="2026-02-07",
            call_number=call_number,
            duration_minutes=profile.target_turn_count,  # rough approximation
            participants=["rep"] + [
                f"prospect_{s.role.lower().replace(' ', '_')}"
                for s in profile.account.stakeholders
            ],
        ),
        utterances=data["utterances"],
    )


_VALID_DIVERGENCE_TYPES = {
    "text_positive_audio_negative",
    "text_negative_audio_positive",
    "text_neutral_audio_negative",
    "text_neutral_audio_positive",
}

# Literal fields that accept low/medium/high — the LLM sometimes invents combos
_LOW_MED_HIGH = {"low", "medium", "high"}


def _clamp_literal(value: str, valid: set[str], default: str) -> str:
    """Map a value to the nearest valid literal, falling back to default."""
    if value in valid:
        return value
    v = value.lower().replace(" ", "").replace("_", "-")
    for candidate in valid:
        if candidate in v:
            return candidate
    return default


def _normalize_ground_truth(data: dict) -> dict:
    """Coerce LLM-generated values to match strict Pydantic schemas."""
    # --- Surface layer ---
    for entity in data.get("surface", {}).get("entities", []):
        if entity.get("mention_count", 1) < 1:
            entity["mention_count"] = 1

    # Clamp all 0-1 float scores across every layer
    _clamp_scores(data.get("surface", {}), {"intensity", "relevance"})
    _clamp_scores(data.get("behavioral", {}), {"confidence"})
    _clamp_scores(data.get("psychographic", {}), {"confidence"})
    _clamp_scores(data.get("multimodal", {}), {"confidence"})

    # --- Behavioral layer ---
    for point in data.get("behavioral", {}).get("engagement_trajectory", []):
        point["energy"] = _clamp_literal(point.get("energy", "medium"), _LOW_MED_HIGH, "medium")
        point["participation_level"] = _clamp_literal(
            point.get("participation_level", "moderate"),
            {"low", "moderate", "high"}, "moderate",
        )
        point.setdefault("question_depth", "moderate")

    # --- Multimodal layer ---
    multimodal = data.get("multimodal")
    if multimodal and "divergences" in multimodal:
        multimodal["divergences"] = [
            d for d in multimodal["divergences"]
            if d.get("type") in _VALID_DIVERGENCE_TYPES
        ]

    return data


def _clamp_scores(layer: dict | None, keys: set[str]) -> None:
    """Recursively clamp float fields in *keys* to [0.0, 1.0]."""
    if layer is None:
        return
    if isinstance(layer, dict):
        for k, v in layer.items():
            if k in keys and isinstance(v, (int, float)):
                layer[k] = max(0.0, min(1.0, float(v)))
            elif isinstance(v, (dict, list)):
                _clamp_scores(v, keys)
    elif isinstance(layer, list):
        for item in layer:
            _clamp_scores(item, keys)


def generate_ground_truth(
    client: anthropic.Anthropic,
    transcript: Transcript,
    profile: GenerationProfile,
) -> ExtractionResult:
    """Generate ground truth extraction annotations for a transcript."""
    transcript_json = transcript.model_dump_json(indent=2)
    prompt = _build_ground_truth_prompt(transcript_json, profile)
    data = _llm_generate_json(client, prompt, max_tokens=16384)
    data = _normalize_ground_truth(data)

    call_id = transcript.call_metadata.call_id
    has_multimodal = profile.include_paralinguistic and data.get("multimodal") is not None

    return ExtractionResult(
        transcript_id=call_id,
        extraction_timestamp="2026-02-07T00:00:00Z",
        surface=data["surface"],
        behavioral=data["behavioral"],
        psychographic=data["psychographic"],
        multimodal=data["multimodal"] if has_multimodal else None,
        overall_confidence=0.9,
        notes=["ground truth annotation — human review recommended"],
    )


def generate_corpus(client: anthropic.Anthropic | None = None) -> None:
    """Generate the full synthetic corpus from all profiles."""
    if client is None:
        client = anthropic.Anthropic()

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    for profile in PROFILES:
        for call_num in range(1, profile.call_count + 1):
            call_id = _call_id(profile, call_num)
            transcript_path = TRANSCRIPTS_DIR / f"{call_id}.json"
            gt_path = GROUND_TRUTH_DIR / f"{call_id}.json"

            if transcript_path.exists() and gt_path.exists():
                print(f"Skipping {call_id} (already generated)")
                continue

            if transcript_path.exists():
                print(f"Loading existing transcript: {call_id}...")
                transcript = Transcript.model_validate_json(transcript_path.read_text())
            else:
                print(f"Generating transcript: {call_id}...")
                transcript = generate_transcript(client, profile, call_num)
                transcript_path.write_text(transcript.model_dump_json(indent=2))
                print(f"  Saved: {transcript_path}")

            print(f"  Generating ground truth for {call_id}...")
            ground_truth = generate_ground_truth(client, transcript, profile)
            gt_path.write_text(ground_truth.model_dump_json(indent=2))
            print(f"  Saved: {gt_path}")

    print(f"\nCorpus complete: {len(list(TRANSCRIPTS_DIR.glob('*.json')))} transcripts generated.")


if __name__ == "__main__":
    generate_corpus()
