"""LLM-as-judge evaluation using rubric-based Likert scoring."""

from __future__ import annotations

import hashlib
import json

import anthropic

from .report import JudgeScore

JUDGE_MODEL = "claude-haiku-4-5-20251001"

# -- Rubric definitions --

ASPECT_GRANULARITY_RUBRIC = """\
5 - Excellent: Aspect is at exactly the right level of granularity (e.g., "pricing" not "cost" or "the 185K annual license pricing"). Captures the precise concept discussed.
4 - Good: Aspect is slightly too broad or narrow but captures the right concept.
3 - Acceptable: Aspect is recognizable but significantly too broad (e.g., "business" instead of "implementation timeline").
2 - Poor: Aspect is misleading or conflates multiple distinct aspects.
1 - Unacceptable: Aspect is completely wrong or nonsensical."""

OBJECTION_TRIPLE_RUBRIC = """\
5 - Excellent: All three components (objection, resolution, outcome) are accurate, specific language closely matches transcript, and source indices are correct.
4 - Good: Components are correct but specific language is paraphrased rather than quoted from the transcript.
3 - Acceptable: Objection and outcome are correct but resolution type or specifics are partially wrong.
2 - Poor: Objection type is correct but resolution or outcome are significantly wrong.
1 - Unacceptable: Objection is misidentified or the triple does not correspond to a real exchange in the transcript."""

PERSONA_REASONING_RUBRIC = """\
5 - Excellent: Reasoning cites specific transcript evidence, correctly maps behavior patterns to archetype definition, and acknowledges nuance.
4 - Good: Reasoning is correct and grounded in the transcript but misses some supporting evidence.
3 - Acceptable: Reasoning reaches the right conclusion but with weak or generic justification.
2 - Poor: Reasoning has logical gaps or cites evidence that does not support the conclusion.
1 - Unacceptable: Reasoning contradicts the transcript or fundamentally mischaracterizes the buyer."""

FRAMING_PATTERN_RUBRIC = """\
5 - Excellent: Patterns are specific, accurate, insightful, and would help a marketer tailor content for this buyer.
4 - Good: Patterns are accurate and somewhat specific but not deeply insightful.
3 - Acceptable: Patterns are generic but not wrong (e.g., "uses business language").
2 - Poor: Patterns are vague or partially inaccurate.
1 - Unacceptable: Patterns are wrong or completely generic."""

COMPETITIVE_CONTEXT_RUBRIC = """\
5 - Excellent: Context captures the full nuance of how the competitor was mentioned — as leverage, genuine alternative, or incumbent — with accurate sentiment and comparison type.
4 - Good: Context is accurate but misses some nuance of the mention.
3 - Acceptable: Context captures the basic mention but mischaracterizes the sentiment or comparison type.
2 - Poor: Context is significantly incomplete or misleading.
1 - Unacceptable: Context is wrong."""

DIVERGENCE_INTERPRETATION_RUBRIC = """\
5 - Excellent: Interpretation correctly synthesizes text content with nonverbal cues, explains the psychological state, and notes business implications.
4 - Good: Interpretation is correct but lacks business implications or is somewhat superficial.
3 - Acceptable: Interpretation is plausible but generic — could apply to many situations, not specific to this moment.
2 - Poor: Interpretation contradicts either the text or the nonverbal cues.
1 - Unacceptable: Interpretation is completely wrong."""


def _build_judge_prompt(
    transcript_excerpt: str,
    signal_json: str,
    ground_truth_json: str,
    rubric: str,
    signal_description: str,
) -> str:
    return f"""\
You are evaluating the quality of a signal extracted from a sales call transcript by an AI system.

## Transcript (relevant excerpt)
{transcript_excerpt}

## Extracted Signal ({signal_description})
{signal_json}

## Ground Truth (reference annotation)
{ground_truth_json}

## Evaluation Rubric
Score from 1 to 5:

{rubric}

## Instructions
1. Read the transcript excerpt carefully
2. Compare the extracted signal against the ground truth
3. Apply the rubric criteria
4. Return ONLY valid JSON: {{"score": <1-5>, "justification": "<2-3 sentences>"}}"""


def _cache_key(transcript_id: str, signal_type: str, signal_data: str) -> str:
    """Create a deterministic cache key from signal identity."""
    h = hashlib.sha256(signal_data.encode()).hexdigest()[:12]
    return f"{transcript_id}:{signal_type}:{h}"


class LLMJudge:
    """Rubric-based LLM evaluator using Claude Haiku for cost efficiency."""

    def __init__(self, client: anthropic.Anthropic | None = None):
        self._client = client or anthropic.Anthropic()
        self._cache: dict[str, JudgeScore] = {}

    def _call(
        self,
        transcript_id: str,
        signal_type: str,
        transcript_excerpt: str,
        signal_json: str,
        ground_truth_json: str,
        rubric: str,
        signal_description: str,
    ) -> JudgeScore:
        key = _cache_key(transcript_id, signal_type, signal_json)
        if key in self._cache:
            return self._cache[key]

        prompt = _build_judge_prompt(
            transcript_excerpt, signal_json, ground_truth_json,
            rubric, signal_description,
        )

        response = self._client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Parse JSON response, handling markdown fences
        text = raw
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        try:
            data = json.loads(text)
            score = JudgeScore(
                score=max(1, min(5, int(data["score"]))),
                justification=str(data.get("justification", "")),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            score = JudgeScore(score=3, justification=f"Parse error: {raw[:200]}")

        self._cache[key] = score
        return score

    def score_aspect_quality(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        aspect_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "aspect", transcript_excerpt,
            aspect_json, ground_truth_json,
            ASPECT_GRANULARITY_RUBRIC, "aspect-based sentiment",
        )

    def score_objection_triple(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        triple_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "objection_triple", transcript_excerpt,
            triple_json, ground_truth_json,
            OBJECTION_TRIPLE_RUBRIC, "objection-resolution-outcome triple",
        )

    def score_persona_reasoning(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        persona_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "persona", transcript_excerpt,
            persona_json, ground_truth_json,
            PERSONA_REASONING_RUBRIC, "persona indicator",
        )

    def score_framing_patterns(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        fingerprint_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "framing", transcript_excerpt,
            fingerprint_json, ground_truth_json,
            FRAMING_PATTERN_RUBRIC, "language fingerprint / framing patterns",
        )

    def score_competitive_context(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        mention_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "competitive", transcript_excerpt,
            mention_json, ground_truth_json,
            COMPETITIVE_CONTEXT_RUBRIC, "competitive mention",
        )

    def score_divergence_interpretation(
        self,
        transcript_id: str,
        transcript_excerpt: str,
        divergence_json: str,
        ground_truth_json: str,
    ) -> JudgeScore:
        return self._call(
            transcript_id, "divergence", transcript_excerpt,
            divergence_json, ground_truth_json,
            DIVERGENCE_INTERPRETATION_RUBRIC, "multimodal divergence",
        )
