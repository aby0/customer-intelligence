"""Evaluation runner — top-level evaluate() and evaluate_corpus() functions."""

from __future__ import annotations

import json

import anthropic

from customer_intelligence.extraction.extractor import _format_transcript
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.transcript import Transcript

from .baselines import (
    BaselineUnavailableError,
    compute_entity_baseline_agreement,
    compute_keyphrase_baseline_agreement,
    compute_sentiment_baseline_agreement,
)
from .llm_judge import LLMJudge
from .report import CorpusReport, EvaluationReport
from .signal_evaluators import (
    BehavioralEvaluator,
    MultimodalEvaluator,
    PsychographicEvaluator,
    SurfaceEvaluator,
)


def evaluate(
    extracted: ExtractionResult,
    ground_truth: ExtractionResult,
    transcript: Transcript,
    *,
    skip_llm_judge: bool = True,
    skip_baselines: bool = False,
    client: anthropic.Anthropic | None = None,
) -> EvaluationReport:
    """Evaluate a single extraction result against ground truth.

    Args:
        extracted: The extraction output to evaluate.
        ground_truth: The reference annotation.
        transcript: The source transcript (needed for structural checks).
        skip_llm_judge: If True (default), skip LLM-as-judge scoring.
        skip_baselines: If True, skip NLP baseline comparisons.
        client: Optional Anthropic client for LLM-as-judge calls.
    """
    # Core metrics (always run)
    surface_report = SurfaceEvaluator().evaluate(
        extracted.surface, ground_truth.surface, transcript,
    )
    behavioral_report = BehavioralEvaluator().evaluate(
        extracted.behavioral, ground_truth.behavioral, transcript,
    )
    psychographic_report = PsychographicEvaluator().evaluate(
        extracted.psychographic, ground_truth.psychographic, transcript,
    )
    multimodal_report = MultimodalEvaluator().evaluate(
        extracted.multimodal, ground_truth.multimodal, transcript,
    )

    # NLP baselines (optional)
    if not skip_baselines:
        _add_baselines(extracted, transcript, surface_report)

    # LLM-as-judge (optional)
    if not skip_llm_judge:
        judge = LLMJudge(client=client)
        transcript_text = _format_transcript(transcript)
        _add_judge_scores(
            judge, extracted, ground_truth,
            transcript.call_metadata.call_id, transcript_text,
            surface_report, behavioral_report, psychographic_report,
            multimodal_report,
        )

    return EvaluationReport(
        transcript_id=extracted.transcript_id,
        surface=surface_report,
        behavioral=behavioral_report,
        psychographic=psychographic_report,
        multimodal=multimodal_report,
    )


def evaluate_corpus(
    cases: list[tuple[ExtractionResult, ExtractionResult, Transcript]],
    *,
    skip_llm_judge: bool = True,
    skip_baselines: bool = False,
    client: anthropic.Anthropic | None = None,
) -> CorpusReport:
    """Evaluate extraction quality across a corpus.

    Args:
        cases: List of (extracted, ground_truth, transcript) triples.
        skip_llm_judge: If True (default), skip LLM-as-judge scoring.
        skip_baselines: If True, skip NLP baseline comparisons.
        client: Optional Anthropic client for LLM-as-judge calls.
    """
    reports = []
    for extracted, ground_truth, transcript in cases:
        report = evaluate(
            extracted, ground_truth, transcript,
            skip_llm_judge=skip_llm_judge,
            skip_baselines=skip_baselines,
            client=client,
        )
        reports.append(report)
    return CorpusReport(reports=reports)


def _add_baselines(
    extracted: ExtractionResult,
    transcript: Transcript,
    surface_report,
) -> None:
    """Add NLP baseline agreement scores to surface metrics."""
    transcript_text = " ".join(u.text for u in transcript.utterances)

    # Entity baseline
    for m in surface_report.signal_metrics:
        if m.signal_name == "entities":
            ext_entities = {e.name.lower() for e in extracted.surface.entities}
            m.baseline_agreement = compute_entity_baseline_agreement(
                ext_entities, transcript_text,
            )

        elif m.signal_name == "key_phrases":
            ext_phrases = {kp.phrase.lower() for kp in extracted.surface.key_phrases}
            m.baseline_agreement = compute_keyphrase_baseline_agreement(
                ext_phrases, transcript_text,
            )

        elif m.signal_name == "aspects":
            # Build (source_text, polarity) pairs for sentiment baseline
            utterance_map = {u.turn_index: u.text for u in transcript.utterances}
            pairs = []
            for a in extracted.surface.aspects:
                source_text = " ".join(
                    utterance_map.get(idx, "")
                    for idx in a.source_utterance_indices
                )
                if source_text.strip():
                    pairs.append((source_text, a.sentiment))
            m.baseline_agreement = compute_sentiment_baseline_agreement(
                pairs, utterance_map,
            )


def _add_judge_scores(
    judge: LLMJudge,
    extracted: ExtractionResult,
    ground_truth: ExtractionResult,
    transcript_id: str,
    transcript_text: str,
    surface_report,
    behavioral_report,
    psychographic_report,
    multimodal_report,
) -> None:
    """Add LLM-as-judge scores to signal metrics."""

    # Aspect quality
    for m in surface_report.signal_metrics:
        if m.signal_name == "aspects":
            for ext_a, gt_a, _ in m.matched_pairs[:5]:  # Limit to 5 to control cost
                ext_obj = next(a for a in extracted.surface.aspects if a.aspect == ext_a)
                gt_obj = next(a for a in ground_truth.surface.aspects if a.aspect == gt_a)
                score = judge.score_aspect_quality(
                    transcript_id, transcript_text,
                    ext_obj.model_dump_json(), gt_obj.model_dump_json(),
                )
                m.judge_scores.append(score)
            if m.judge_scores:
                m.mean_judge_score = (
                    sum(js.score for js in m.judge_scores) / len(m.judge_scores)
                )

    # Objection triple completeness
    for m in behavioral_report.signal_metrics:
        if m.signal_name == "objection_triples":
            for ext_t in extracted.behavioral.objection_triples[:5]:
                gt_matches = [
                    t for t in ground_truth.behavioral.objection_triples
                    if t.objection.type == ext_t.objection.type
                ]
                gt_json = gt_matches[0].model_dump_json() if gt_matches else "{}"
                score = judge.score_objection_triple(
                    transcript_id, transcript_text,
                    ext_t.model_dump_json(), gt_json,
                )
                m.judge_scores.append(score)
            if m.judge_scores:
                m.mean_judge_score = (
                    sum(js.score for js in m.judge_scores) / len(m.judge_scores)
                )

        elif m.signal_name == "competitive_mentions":
            for ext_cm in extracted.behavioral.competitive_mentions[:3]:
                gt_matches = [
                    cm for cm in ground_truth.behavioral.competitive_mentions
                    if cm.competitor.lower() == ext_cm.competitor.lower()
                ]
                gt_json = gt_matches[0].model_dump_json() if gt_matches else "{}"
                score = judge.score_competitive_context(
                    transcript_id, transcript_text,
                    ext_cm.model_dump_json(), gt_json,
                )
                m.judge_scores.append(score)
            if m.judge_scores:
                m.mean_judge_score = (
                    sum(js.score for js in m.judge_scores) / len(m.judge_scores)
                )

    # Persona reasoning
    for m in psychographic_report.signal_metrics:
        if m.signal_name == "persona_indicators":
            for ext_pi in extracted.psychographic.persona_indicators:
                gt_matches = [
                    pi for pi in ground_truth.psychographic.persona_indicators
                    if pi.archetype == ext_pi.archetype
                ]
                gt_json = gt_matches[0].model_dump_json() if gt_matches else "{}"
                score = judge.score_persona_reasoning(
                    transcript_id, transcript_text,
                    ext_pi.model_dump_json(), gt_json,
                )
                m.judge_scores.append(score)
            if m.judge_scores:
                m.mean_judge_score = (
                    sum(js.score for js in m.judge_scores) / len(m.judge_scores)
                )

        elif m.signal_name == "language_fingerprint":
            ext_fp = extracted.psychographic.language_fingerprint
            gt_fp = ground_truth.psychographic.language_fingerprint
            score = judge.score_framing_patterns(
                transcript_id, transcript_text,
                ext_fp.model_dump_json(), gt_fp.model_dump_json(),
            )
            m.judge_scores.append(score)
            m.mean_judge_score = float(score.score)

    # Divergence interpretation
    if multimodal_report and extracted.multimodal and ground_truth.multimodal:
        for m in multimodal_report.signal_metrics:
            if m.signal_name == "divergences":
                for ext_d in extracted.multimodal.divergences[:5]:
                    gt_matches = [
                        d for d in ground_truth.multimodal.divergences
                        if d.utterance_index == ext_d.utterance_index
                    ]
                    gt_json = gt_matches[0].model_dump_json() if gt_matches else "{}"
                    score = judge.score_divergence_interpretation(
                        transcript_id, transcript_text,
                        ext_d.model_dump_json(), gt_json,
                    )
                    m.judge_scores.append(score)
                if m.judge_scores:
                    m.mean_judge_score = (
                        sum(js.score for js in m.judge_scores) / len(m.judge_scores)
                    )
