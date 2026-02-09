"""Per-signal-type evaluators that compose metrics, fuzzy matching, and structural checks."""

from __future__ import annotations

from customer_intelligence.schemas.behavioral import BehavioralSignals
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.multimodal import MultimodalSignals
from customer_intelligence.schemas.psychographic import PsychographicSignals
from customer_intelligence.schemas.surface import SurfaceSignals
from customer_intelligence.schemas.transcript import Transcript

from . import fuzzy_matching as fm
from . import metrics
from .report import LayerReport, SignalMetrics
from .structural_checks import (
    check_score_distribution,
    check_timeline_consistency,
    validate_utterance_indices,
)

# -- Fuzzy match thresholds per signal type --
ENTITY_THRESHOLD = 0.8
TOPIC_THRESHOLD = 0.5
ASPECT_THRESHOLD = 0.6
KEYPHRASE_THRESHOLD = 0.4
VOCABULARY_THRESHOLD = 0.8
METAPHOR_THRESHOLD = 0.5


class SurfaceEvaluator:
    """Evaluate Layer 1 surface signal extraction."""

    def evaluate(
        self,
        extracted: SurfaceSignals,
        ground_truth: SurfaceSignals,
        transcript: Transcript,
    ) -> LayerReport:
        max_idx = max((u.turn_index for u in transcript.utterances), default=0)

        return LayerReport(
            layer_name="Surface",
            signal_metrics=[
                self._eval_aspects(extracted, ground_truth, max_idx),
                self._eval_topics(extracted, ground_truth, transcript),
                self._eval_entities(extracted, ground_truth),
                self._eval_key_phrases(extracted, ground_truth),
            ],
        )

    def _eval_aspects(
        self, extracted: SurfaceSignals, ground_truth: SurfaceSignals, max_idx: int,
    ) -> SignalMetrics:
        ext_names = [a.aspect for a in extracted.aspects]
        gt_names = [a.aspect for a in ground_truth.aspects]

        p, r, f, matched = fm.compute_fuzzy_precision_recall(
            ext_names, gt_names, fm.token_overlap_similarity, ASPECT_THRESHOLD,
        )

        # Sentiment polarity agreement on matched pairs
        polarity_matches = 0
        intensity_errors: list[float] = []
        for ext_str, gt_str, _ in matched:
            ext_aspect = next(a for a in extracted.aspects if a.aspect == ext_str)
            gt_aspect = next(a for a in ground_truth.aspects if a.aspect == gt_str)
            if ext_aspect.sentiment == gt_aspect.sentiment:
                polarity_matches += 1
            intensity_errors.append(abs(ext_aspect.intensity - gt_aspect.intensity))

        polarity_accuracy = polarity_matches / len(matched) if matched else None
        intensity_mae = (
            sum(intensity_errors) / len(intensity_errors) if intensity_errors else None
        )

        # Structural: validate source utterance indices
        issues = []
        for a in extracted.aspects:
            issues.extend(
                validate_utterance_indices(a.source_utterance_indices, max_idx, f"aspect:{a.aspect}")
            )

        # Intensity score distribution
        intensities = [a.intensity for a in extracted.aspects]
        dist = check_score_distribution(intensities, "aspect_intensity")
        issues.extend(dist.get("issues", []))

        return SignalMetrics(
            signal_name="aspects",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(ext_names),
            count_ground_truth=len(gt_names),
            accuracy=polarity_accuracy,
            mae=intensity_mae,
            structural_issues=issues,
            score_distribution=dist,
            matched_pairs=matched,
        )

    def _eval_topics(
        self,
        extracted: SurfaceSignals,
        ground_truth: SurfaceSignals,
        transcript: Transcript,
    ) -> SignalMetrics:
        ext_names = [t.name for t in extracted.topics]
        gt_names = [t.name for t in ground_truth.topics]

        p, r, f, matched = fm.compute_fuzzy_precision_recall(
            ext_names, gt_names, fm.token_overlap_similarity, TOPIC_THRESHOLD,
        )

        # Timeline position accuracy on matched pairs
        timeline_matches = 0
        relevance_errors: list[float] = []
        for ext_str, gt_str, _ in matched:
            ext_topic = next(t for t in extracted.topics if t.name == ext_str)
            gt_topic = next(t for t in ground_truth.topics if t.name == gt_str)
            if ext_topic.timeline_position == gt_topic.timeline_position:
                timeline_matches += 1
            relevance_errors.append(abs(ext_topic.relevance - gt_topic.relevance))

        timeline_accuracy = timeline_matches / len(matched) if matched else None
        relevance_mae = (
            sum(relevance_errors) / len(relevance_errors) if relevance_errors else None
        )

        # Structural: timeline consistency with transcript text
        issues = check_timeline_consistency(extracted.topics, transcript.utterances)

        # Relevance score distribution
        relevances = [t.relevance for t in extracted.topics]
        dist = check_score_distribution(relevances, "topic_relevance")
        issues.extend(dist.get("issues", []))

        return SignalMetrics(
            signal_name="topics",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(ext_names),
            count_ground_truth=len(gt_names),
            accuracy=timeline_accuracy,
            mae=relevance_mae,
            structural_issues=issues,
            score_distribution=dist,
            matched_pairs=matched,
        )

    def _eval_entities(
        self, extracted: SurfaceSignals, ground_truth: SurfaceSignals,
    ) -> SignalMetrics:
        ext_names = [e.name for e in extracted.entities]
        gt_names = [e.name for e in ground_truth.entities]

        p, r, f, matched = fm.compute_fuzzy_precision_recall(
            ext_names, gt_names, fm.token_overlap_similarity, ENTITY_THRESHOLD,
        )

        # Entity type accuracy on matched pairs
        type_matches = 0
        for ext_str, gt_str, _ in matched:
            ext_ent = next(e for e in extracted.entities if e.name == ext_str)
            gt_ent = next(e for e in ground_truth.entities if e.name == gt_str)
            if ext_ent.entity_type == gt_ent.entity_type:
                type_matches += 1

        type_accuracy = type_matches / len(matched) if matched else None

        return SignalMetrics(
            signal_name="entities",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(ext_names),
            count_ground_truth=len(gt_names),
            accuracy=type_accuracy,
            matched_pairs=matched,
        )

    def _eval_key_phrases(
        self, extracted: SurfaceSignals, ground_truth: SurfaceSignals,
    ) -> SignalMetrics:
        ext_phrases = [kp.phrase for kp in extracted.key_phrases]
        gt_phrases = [kp.phrase for kp in ground_truth.key_phrases]

        p, r, f, matched = fm.compute_fuzzy_precision_recall(
            ext_phrases, gt_phrases, fm.token_overlap_similarity, KEYPHRASE_THRESHOLD,
        )

        # Relevance MAE on matched pairs
        relevance_errors: list[float] = []
        for ext_str, gt_str, _ in matched:
            ext_kp = next(kp for kp in extracted.key_phrases if kp.phrase == ext_str)
            gt_kp = next(kp for kp in ground_truth.key_phrases if kp.phrase == gt_str)
            relevance_errors.append(abs(ext_kp.relevance - gt_kp.relevance))

        relevance_mae = (
            sum(relevance_errors) / len(relevance_errors) if relevance_errors else None
        )

        # Relevance distribution
        relevances = [kp.relevance for kp in extracted.key_phrases]
        dist = check_score_distribution(relevances, "keyphrase_relevance")

        return SignalMetrics(
            signal_name="key_phrases",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(ext_phrases),
            count_ground_truth=len(gt_phrases),
            mae=relevance_mae,
            score_distribution=dist,
            structural_issues=dist.get("issues", []),
            matched_pairs=matched,
        )


class BehavioralEvaluator:
    """Evaluate Layer 2 behavioral signal extraction."""

    def evaluate(
        self,
        extracted: BehavioralSignals,
        ground_truth: BehavioralSignals,
        transcript: Transcript,
    ) -> LayerReport:
        max_idx = max((u.turn_index for u in transcript.utterances), default=0)

        return LayerReport(
            layer_name="Behavioral",
            signal_metrics=[
                self._eval_objection_triples(extracted, ground_truth, max_idx),
                self._eval_buying_intent(extracted, ground_truth),
                self._eval_competitive_mentions(extracted, ground_truth, max_idx),
                self._eval_engagement_trajectory(extracted, ground_truth),
            ],
        )

    def _eval_objection_triples(
        self,
        extracted: BehavioralSignals,
        ground_truth: BehavioralSignals,
        max_idx: int,
    ) -> SignalMetrics:
        ext_types = {t.objection.type for t in extracted.objection_triples}
        gt_types = {t.objection.type for t in ground_truth.objection_triples}

        p, r, f = metrics.precision_recall_f1(ext_types, gt_types)

        # Resolution type accuracy for matched objection types
        resolution_matches = 0
        outcome_matches = 0
        matched_count = 0
        for gt_triple in ground_truth.objection_triples:
            for ext_triple in extracted.objection_triples:
                if ext_triple.objection.type == gt_triple.objection.type:
                    matched_count += 1
                    if (
                        ext_triple.resolution
                        and gt_triple.resolution
                        and ext_triple.resolution.type == gt_triple.resolution.type
                    ):
                        resolution_matches += 1
                    if ext_triple.outcome.resolved == gt_triple.outcome.resolved:
                        outcome_matches += 1
                    break

        resolution_accuracy = resolution_matches / matched_count if matched_count else None
        outcome_accuracy = outcome_matches / matched_count if matched_count else None

        # Structural: validate source indices
        issues = []
        for t in extracted.objection_triples:
            issues.extend(
                validate_utterance_indices(
                    t.objection.source_utterance_indices, max_idx,
                    f"objection:{t.objection.type}",
                )
            )
            if t.resolution:
                issues.extend(
                    validate_utterance_indices(
                        t.resolution.source_utterance_indices, max_idx,
                        f"resolution:{t.resolution.type}",
                    )
                )

        # Confidence distribution
        confidences = [t.confidence for t in extracted.objection_triples]
        dist = check_score_distribution(confidences, "objection_confidence")
        issues.extend(dist.get("issues", []))

        # Combine resolution and outcome accuracy into a single accuracy score
        combined_accuracy = None
        if resolution_accuracy is not None and outcome_accuracy is not None:
            combined_accuracy = (resolution_accuracy + outcome_accuracy) / 2

        return SignalMetrics(
            signal_name="objection_triples",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.objection_triples),
            count_ground_truth=len(ground_truth.objection_triples),
            accuracy=combined_accuracy,
            structural_issues=issues,
            score_distribution=dist,
        )

    def _eval_buying_intent(
        self, extracted: BehavioralSignals, ground_truth: BehavioralSignals,
    ) -> SignalMetrics:
        ext_types = {m.type for m in extracted.buying_intent_markers}
        gt_types = {m.type for m in ground_truth.buying_intent_markers}

        p, r, f = metrics.precision_recall_f1(ext_types, gt_types)

        # Confidence distribution
        confidences = [m.confidence for m in extracted.buying_intent_markers]
        dist = check_score_distribution(confidences, "buying_intent_confidence")

        return SignalMetrics(
            signal_name="buying_intent",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.buying_intent_markers),
            count_ground_truth=len(ground_truth.buying_intent_markers),
            score_distribution=dist,
            structural_issues=dist.get("issues", []),
        )

    def _eval_competitive_mentions(
        self,
        extracted: BehavioralSignals,
        ground_truth: BehavioralSignals,
        max_idx: int,
    ) -> SignalMetrics:
        ext_names = {cm.competitor.lower() for cm in extracted.competitive_mentions}
        gt_names = {cm.competitor.lower() for cm in ground_truth.competitive_mentions}

        p, r, f = metrics.precision_recall_f1(ext_names, gt_names)

        # Sentiment accuracy on matched competitors
        sentiment_matches = 0
        matched_count = 0
        for gt_cm in ground_truth.competitive_mentions:
            for ext_cm in extracted.competitive_mentions:
                if ext_cm.competitor.lower() == gt_cm.competitor.lower():
                    matched_count += 1
                    if ext_cm.sentiment == gt_cm.sentiment:
                        sentiment_matches += 1
                    break

        sentiment_accuracy = sentiment_matches / matched_count if matched_count else None

        # Structural: validate source indices
        issues = []
        for cm in extracted.competitive_mentions:
            issues.extend(
                validate_utterance_indices(
                    cm.source_utterance_indices, max_idx,
                    f"competitor:{cm.competitor}",
                )
            )

        return SignalMetrics(
            signal_name="competitive_mentions",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.competitive_mentions),
            count_ground_truth=len(ground_truth.competitive_mentions),
            accuracy=sentiment_accuracy,
            structural_issues=issues,
        )

    def _eval_engagement_trajectory(
        self, extracted: BehavioralSignals, ground_truth: BehavioralSignals,
    ) -> SignalMetrics:
        # Phase coverage
        ext_phases = {p.phase for p in extracted.engagement_trajectory}
        gt_phases = {p.phase for p in ground_truth.engagement_trajectory}
        p, r, f = metrics.precision_recall_f1(ext_phases, gt_phases)

        # Ordinal agreement on matched phases
        participation_scale = ["low", "moderate", "high"]
        depth_scale = ["surface", "moderate", "deep"]
        energy_scale = ["low", "medium", "high"]

        agreements: list[float] = []
        for gt_point in ground_truth.engagement_trajectory:
            for ext_point in extracted.engagement_trajectory:
                if ext_point.phase == gt_point.phase:
                    agreements.append(
                        metrics.ordinal_agreement(
                            ext_point.participation_level,
                            gt_point.participation_level,
                            participation_scale,
                        )
                    )
                    agreements.append(
                        metrics.ordinal_agreement(
                            ext_point.question_depth,
                            gt_point.question_depth,
                            depth_scale,
                        )
                    )
                    agreements.append(
                        metrics.ordinal_agreement(
                            ext_point.energy, gt_point.energy, energy_scale,
                        )
                    )
                    break

        mean_agreement = sum(agreements) / len(agreements) if agreements else None

        return SignalMetrics(
            signal_name="engagement_trajectory",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.engagement_trajectory),
            count_ground_truth=len(ground_truth.engagement_trajectory),
            ordinal_agreement=mean_agreement,
        )


class PsychographicEvaluator:
    """Evaluate Layer 3 psychographic signal extraction."""

    def evaluate(
        self,
        extracted: PsychographicSignals,
        ground_truth: PsychographicSignals,
        transcript: Transcript,
    ) -> LayerReport:
        return LayerReport(
            layer_name="Psychographic",
            signal_metrics=[
                self._eval_mental_model(extracted, ground_truth),
                self._eval_persona_indicators(extracted, ground_truth),
                self._eval_language_fingerprint(extracted, ground_truth),
            ],
        )

    def _eval_mental_model(
        self, extracted: PsychographicSignals, ground_truth: PsychographicSignals,
    ) -> SignalMetrics:
        primary_match = 1.0 if extracted.mental_model.primary == ground_truth.mental_model.primary else 0.0

        secondary_match = None
        if ground_truth.mental_model.secondary is not None:
            secondary_match = (
                1.0
                if extracted.mental_model.secondary == ground_truth.mental_model.secondary
                else 0.0
            )

        confidence_delta = abs(
            extracted.mental_model.confidence - ground_truth.mental_model.confidence
        )

        # Evidence overlap (token-level)
        ext_evidence = " ".join(extracted.mental_model.evidence)
        gt_evidence = " ".join(ground_truth.mental_model.evidence)
        evidence_sim = fm.token_overlap_similarity(ext_evidence, gt_evidence)

        accuracy = primary_match
        if secondary_match is not None:
            accuracy = (primary_match + secondary_match) / 2

        return SignalMetrics(
            signal_name="mental_model",
            precision=primary_match,
            recall=primary_match,
            f1=primary_match,
            count_extracted=1,
            count_ground_truth=1,
            accuracy=accuracy,
            mae=confidence_delta,
        )

    def _eval_persona_indicators(
        self, extracted: PsychographicSignals, ground_truth: PsychographicSignals,
    ) -> SignalMetrics:
        ext_archetypes = {pi.archetype for pi in extracted.persona_indicators}
        gt_archetypes = {pi.archetype for pi in ground_truth.persona_indicators}

        p, r, f = metrics.precision_recall_f1(ext_archetypes, gt_archetypes)

        # Confidence delta for matched archetypes
        confidence_errors: list[float] = []
        for gt_pi in ground_truth.persona_indicators:
            for ext_pi in extracted.persona_indicators:
                if ext_pi.archetype == gt_pi.archetype:
                    confidence_errors.append(abs(ext_pi.confidence - gt_pi.confidence))
                    break

        mae = (
            sum(confidence_errors) / len(confidence_errors) if confidence_errors else None
        )

        # Confidence distribution
        confidences = [pi.confidence for pi in extracted.persona_indicators]
        dist = check_score_distribution(confidences, "persona_confidence")

        return SignalMetrics(
            signal_name="persona_indicators",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.persona_indicators),
            count_ground_truth=len(ground_truth.persona_indicators),
            mae=mae,
            score_distribution=dist,
            structural_issues=dist.get("issues", []),
        )

    def _eval_language_fingerprint(
        self, extracted: PsychographicSignals, ground_truth: PsychographicSignals,
    ) -> SignalMetrics:
        ext_fp = extracted.language_fingerprint
        gt_fp = ground_truth.language_fingerprint

        # Vocabulary overlap (exact, lowercased)
        ext_vocab = {v.lower() for v in ext_fp.distinctive_vocabulary}
        gt_vocab = {v.lower() for v in gt_fp.distinctive_vocabulary}
        vocab_p, vocab_r, vocab_f = metrics.precision_recall_f1(ext_vocab, gt_vocab)

        # Metaphor overlap (fuzzy)
        meta_p, meta_r, meta_f, meta_matched = fm.compute_fuzzy_precision_recall(
            ext_fp.metaphors, gt_fp.metaphors,
            fm.token_overlap_similarity, METAPHOR_THRESHOLD,
        )

        # Framing pattern overlap (fuzzy)
        frame_p, frame_r, frame_f, _ = fm.compute_fuzzy_precision_recall(
            ext_fp.framing_patterns, gt_fp.framing_patterns,
            fm.token_overlap_similarity, METAPHOR_THRESHOLD,
        )

        # Average across the three sub-signals
        all_p = [x for x in [vocab_p, meta_p, frame_p] if x is not None]
        all_r = [x for x in [vocab_r, meta_r, frame_r] if x is not None]
        all_f = [x for x in [vocab_f, meta_f, frame_f] if x is not None]

        avg_p = sum(all_p) / len(all_p) if all_p else None
        avg_r = sum(all_r) / len(all_r) if all_r else None
        avg_f = sum(all_f) / len(all_f) if all_f else None

        return SignalMetrics(
            signal_name="language_fingerprint",
            precision=avg_p,
            recall=avg_r,
            f1=avg_f,
            count_extracted=(
                len(ext_fp.distinctive_vocabulary)
                + len(ext_fp.metaphors)
                + len(ext_fp.framing_patterns)
            ),
            count_ground_truth=(
                len(gt_fp.distinctive_vocabulary)
                + len(gt_fp.metaphors)
                + len(gt_fp.framing_patterns)
            ),
            matched_pairs=meta_matched,
        )


class MultimodalEvaluator:
    """Evaluate multimodal divergence detection."""

    def evaluate(
        self,
        extracted: MultimodalSignals | None,
        ground_truth: MultimodalSignals | None,
        transcript: Transcript,
    ) -> LayerReport | None:
        if ground_truth is None and extracted is None:
            return None
        if ground_truth is None:
            # Extraction produced multimodal when it shouldn't have
            return LayerReport(
                layer_name="Multimodal",
                signal_metrics=[
                    SignalMetrics(
                        signal_name="divergences",
                        precision=0.0,
                        recall=1.0,
                        f1=0.0,
                        count_extracted=len(extracted.divergences) if extracted else 0,
                        count_ground_truth=0,
                        structural_issues=["Multimodal signals produced but not expected"],
                    ),
                ],
            )
        if extracted is None:
            return LayerReport(
                layer_name="Multimodal",
                signal_metrics=[
                    SignalMetrics(
                        signal_name="divergences",
                        precision=0.0,
                        recall=0.0,
                        f1=0.0,
                        count_extracted=0,
                        count_ground_truth=len(ground_truth.divergences),
                        structural_issues=["Multimodal signals expected but not produced"],
                    ),
                ],
            )

        max_idx = max((u.turn_index for u in transcript.utterances), default=0)

        return LayerReport(
            layer_name="Multimodal",
            signal_metrics=[
                self._eval_divergences(extracted, ground_truth, max_idx),
                self._eval_composite_sentiments(extracted, ground_truth),
            ],
        )

    def _eval_divergences(
        self,
        extracted: MultimodalSignals,
        ground_truth: MultimodalSignals,
        max_idx: int,
    ) -> SignalMetrics:
        ext_indices = {d.utterance_index for d in extracted.divergences}
        gt_indices = {d.utterance_index for d in ground_truth.divergences}

        p, r, f = metrics.precision_recall_f1(ext_indices, gt_indices)

        # Divergence type accuracy on matched indices
        type_matches = 0
        matched_count = 0
        for gt_d in ground_truth.divergences:
            for ext_d in extracted.divergences:
                if ext_d.utterance_index == gt_d.utterance_index:
                    matched_count += 1
                    if ext_d.type == gt_d.type:
                        type_matches += 1
                    break

        type_accuracy = type_matches / matched_count if matched_count else None

        # Structural: validate indices
        issues = validate_utterance_indices(
            [d.utterance_index for d in extracted.divergences], max_idx, "divergence",
        )

        return SignalMetrics(
            signal_name="divergences",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.divergences),
            count_ground_truth=len(ground_truth.divergences),
            accuracy=type_accuracy,
            structural_issues=issues,
        )

    def _eval_composite_sentiments(
        self, extracted: MultimodalSignals, ground_truth: MultimodalSignals,
    ) -> SignalMetrics:
        ext_indices = {cs.utterance_index for cs in extracted.composite_sentiments}
        gt_indices = {cs.utterance_index for cs in ground_truth.composite_sentiments}

        p, r, f = metrics.precision_recall_f1(ext_indices, gt_indices)

        # Polarity accuracy on matched indices
        polarity_matches = 0
        matched_count = 0
        for gt_cs in ground_truth.composite_sentiments:
            for ext_cs in extracted.composite_sentiments:
                if ext_cs.utterance_index == gt_cs.utterance_index:
                    matched_count += 1
                    if ext_cs.adjusted_polarity == gt_cs.adjusted_polarity:
                        polarity_matches += 1
                    break

        polarity_accuracy = polarity_matches / matched_count if matched_count else None

        return SignalMetrics(
            signal_name="composite_sentiments",
            precision=p,
            recall=r,
            f1=f,
            count_extracted=len(extracted.composite_sentiments),
            count_ground_truth=len(ground_truth.composite_sentiments),
            accuracy=polarity_accuracy,
        )
