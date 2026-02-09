"""Rendering components for the Streamlit demo app."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from customer_intelligence.schemas.behavioral import BehavioralSignals
from customer_intelligence.schemas.extraction import ExtractionResult
from customer_intelligence.schemas.multimodal import MultimodalSignals
from customer_intelligence.schemas.psychographic import PsychographicSignals
from customer_intelligence.schemas.summary import TranscriptSummary
from customer_intelligence.schemas.surface import SurfaceSignals
from customer_intelligence.schemas.transcript import Transcript


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTIMENT_COLORS = {
    "positive": "#22c55e",
    "negative": "#ef4444",
    "mixed": "#f59e0b",
    "neutral": "#94a3b8",
}

_MOMENT_ICONS = {
    "breakthrough": "**Breakthrough**",
    "objection": "**Objection**",
    "commitment": "**Commitment**",
    "risk": "**Risk**",
    "insight": "**Insight**",
}


def _resolve_speakers(transcript: Transcript) -> dict[str, str]:
    """Map raw participant keys to readable names like 'David Chen (CFO)'."""
    speaker_map: dict[str, str] = {}
    for participant in transcript.call_metadata.participants:
        if participant == "rep":
            speaker_map["rep"] = "Sales Rep"
            continue
        for s in transcript.account.stakeholders:
            role_key = s.role.lower().replace(" ", "_")
            if role_key in participant:
                speaker_map[participant] = f"{s.name} ({s.role})"
                break
        if participant not in speaker_map:
            speaker_map[participant] = participant.replace("_", " ").title()
    return speaker_map


def _fmt(text: str) -> str:
    """Format snake_case to Title Case."""
    return text.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Tab: Summary
# ---------------------------------------------------------------------------

def render_summary(summary: TranscriptSummary) -> None:
    st.subheader("Executive Summary")
    st.markdown(summary.executive_summary)

    st.subheader("Key Moments")
    for moment in summary.key_moments:
        icon = _MOMENT_ICONS.get(moment.moment_type, f"**{_fmt(moment.moment_type)}**")
        with st.container(border=True):
            st.markdown(f"{icon} &mdash; {moment.description}")
            st.caption(f"Significance: {moment.significance} &bull; Turns: {moment.turn_indices}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Prospect Priorities")
        for p in summary.prospect_priorities:
            st.markdown(f"- {p}")
    with col2:
        st.subheader("Concerns to Address")
        if summary.concerns_to_address:
            for c in summary.concerns_to_address:
                st.markdown(f"- {c}")
        else:
            st.caption("No concerns identified.")

    if summary.action_items:
        st.subheader("Action Items")
        data = [
            {"Action": a.action, "Owner": a.owner, "Criticality": a.criticality.upper()}
            for a in summary.action_items
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tab: Pipeline Overview
# ---------------------------------------------------------------------------


def render_pipeline_overview(
    extraction: ExtractionResult | None,
    transcript: Transcript,
) -> None:
    """Render the Pipeline Overview tab — static explanation + dynamic signal counts."""

    st.subheader("How the Pipeline Works")
    st.markdown(
        "The Customer Intelligence Pipeline processes a sales call transcript "
        "through **multi-layer signal extraction** — analyzing what was said, "
        "how the conversation unfolded, and what it reveals about the buyer's "
        "psychology. Each layer builds on the previous one, producing increasingly "
        "valuable intelligence."
    )

    st.markdown("---")
    st.markdown("#### Signals Extracted from This Call")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("**Layer 1: Surface Signals**")
            st.caption(
                "What topics came up, what entities were mentioned, "
                "and how the prospect feels about each aspect."
            )
            if extraction:
                c1, c2 = st.columns(2)
                c1.metric("Aspects", len(extraction.surface.aspects))
                c2.metric("Topics", len(extraction.surface.topics))
                c3, c4 = st.columns(2)
                c3.metric("Entities", len(extraction.surface.entities))
                c4.metric("Key Phrases", len(extraction.surface.key_phrases))
            else:
                st.caption("No extraction data available.")

    with col2:
        with st.container(border=True):
            st.markdown("**Layer 2: Behavioral Signals**")
            st.caption(
                "How the conversation unfolded — objections raised, "
                "buying intent cues, and engagement shifts."
            )
            if extraction:
                c1, c2 = st.columns(2)
                c1.metric("Objections", len(extraction.behavioral.objection_triples))
                c2.metric("Intent Markers", len(extraction.behavioral.buying_intent_markers))
                c3, c4 = st.columns(2)
                c3.metric("Competitors", len(extraction.behavioral.competitive_mentions))
                c4.metric("Engagement Phases", len(extraction.behavioral.engagement_trajectory))
            else:
                st.caption("No extraction data available.")

    with col3:
        with st.container(border=True):
            st.markdown("**Layer 3: Psychographic Signals**")
            st.caption(
                "What the conversation reveals about how the buyer "
                "thinks, decides, and talks."
            )
            if extraction:
                mm = extraction.psychographic.mental_model
                st.metric("Mental Model", _fmt(mm.primary))
                if extraction.psychographic.persona_indicators:
                    top_persona = max(
                        extraction.psychographic.persona_indicators,
                        key=lambda p: p.confidence,
                    )
                    st.metric("Top Persona", _fmt(top_persona.archetype))
                else:
                    st.metric("Top Persona", "N/A")
                st.metric(
                    "Vocab Fingerprint",
                    f"{len(extraction.psychographic.language_fingerprint.distinctive_vocabulary)} terms",
                )
            else:
                st.caption("No extraction data available.")

    # --- Multimodal section ---
    st.markdown("---")
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.markdown("#### Multimodal Analysis")
        if extraction and extraction.multimodal:
            st.metric("Divergences Detected", len(extraction.multimodal.divergences))
            st.metric("Adjusted Sentiments", len(extraction.multimodal.composite_sentiments))
        else:
            has_para = any(u.paralinguistic is not None for u in transcript.utterances)
            if has_para:
                st.caption("Paralinguistic data available but not yet analyzed.")
            else:
                st.caption("No paralinguistic annotations in this transcript.")

    with col_m2:
        st.markdown(
            "When audio/video cues are available, the pipeline detects "
            "**text-audio divergence** — cases where what the customer says "
            "contradicts how they say it. Hidden objections, polite deflections, "
            "and genuine enthusiasm all leave different multimodal signatures."
        )

    # --- Overall confidence ---
    if extraction:
        st.markdown("---")
        st.markdown("#### Pipeline Confidence")
        st.progress(
            extraction.overall_confidence,
            text=f"Overall extraction confidence: {extraction.overall_confidence:.0%}",
        )

    # --- Navigation hint ---
    st.markdown("---")
    st.info(
        "Use the tabs above to explore each signal layer in detail. "
        "The **Call Summary** tab provides an executive overview, "
        "then each subsequent tab dives into a specific signal layer."
    )


# ---------------------------------------------------------------------------
# Tab: Conversation
# ---------------------------------------------------------------------------

def render_conversation(transcript: Transcript) -> None:
    speaker_map = _resolve_speakers(transcript)

    with st.container(height=600):
        for u in transcript.utterances:
            name = speaker_map.get(u.speaker, u.speaker)
            is_rep = u.speaker == "rep"
            with st.chat_message("assistant" if is_rep else "user"):
                st.markdown(f"**{name}** &mdash; Turn {u.turn_index}")
                st.markdown(u.text)

                if u.paralinguistic:
                    tags = []
                    p = u.paralinguistic
                    if p.pause_before_sec:
                        tags.append(f"{p.pause_before_sec}s pause")
                    if p.energy:
                        tags.append(f"energy: {p.energy}")
                    if p.pitch:
                        tags.append(f"pitch: {p.pitch}")
                    if p.hesitation_markers:
                        tags.append(f"hesitation: {', '.join(p.hesitation_markers)}")
                    if p.tone:
                        tags.append(f"tone: {p.tone}")
                    if p.behaviors:
                        tags.append(f"{', '.join(p.behaviors)}")
                    if tags:
                        st.caption(" | ".join(tags))


# ---------------------------------------------------------------------------
# Tab: Surface Signals
# ---------------------------------------------------------------------------

def render_surface(surface: SurfaceSignals) -> None:
    # Aspect Sentiment
    st.subheader("Aspect Sentiment")
    st.caption("What the prospect cares about and how they feel about each topic.")
    if surface.aspects:
        data = [
            {
                "Aspect": _fmt(a.aspect),
                "Intensity": a.intensity,
                "Sentiment": a.sentiment.title(),
                "Context": a.context or "",
            }
            for a in surface.aspects
        ]
        fig = px.bar(
            data,
            y="Aspect",
            x="Intensity",
            color="Sentiment",
            orientation="h",
            color_discrete_map={k.title(): v for k, v in _SENTIMENT_COLORS.items()},
            hover_data=["Context"],
        )
        fig.update_layout(
            height=max(300, len(data) * 50),
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Topics
    st.subheader("Topics Discussed")
    st.caption("Primary topics and when they appeared in the conversation.")
    if surface.topics:
        data = [
            {
                "Topic": _fmt(t.name),
                "Timeline": _fmt(t.timeline_position),
                "Relevance": f"{t.relevance:.0%}",
            }
            for t in surface.topics
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    # Entities and Key Phrases side by side
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Named Entities")
        if surface.entities:
            data = [
                {
                    "Name": e.name,
                    "Type": _fmt(e.entity_type),
                    "Role": e.role or "",
                    "Mentions": e.mention_count,
                }
                for e in sorted(surface.entities, key=lambda x: x.mention_count, reverse=True)
            ]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Key Phrases")
        if surface.key_phrases:
            for kp in sorted(surface.key_phrases, key=lambda x: x.relevance, reverse=True):
                st.markdown(f"- **{kp.phrase}** ({kp.relevance:.0%})")


# ---------------------------------------------------------------------------
# Tab: Behavioral Signals
# ---------------------------------------------------------------------------

def render_behavioral(behavioral: BehavioralSignals, transcript: Transcript) -> None:
    # Objection Triples
    st.subheader("Objection Flow")
    st.caption(
        "Objection patterns reveal which concerns block deals and how effectively "
        "the sales team resolves them."
    )
    for i, triple in enumerate(behavioral.objection_triples):
        obj = triple.objection
        res = triple.resolution
        out = triple.outcome
        with st.container(border=True):
            st.markdown(f"**Objection {i + 1}** &mdash; {_fmt(obj.type)}")
            c1, c2, c3 = st.columns([3, 3, 2])
            with c1:
                st.markdown("**Concern Raised**")
                st.caption(f"Stage: {_fmt(obj.conversation_stage)} | Speaker: {_fmt(obj.speaker_role)}")
                st.info(f'"{obj.specific_language}"')
            with c2:
                st.markdown("**Resolution Approach**")
                if res:
                    st.caption(f"Strategy: {_fmt(res.type)}")
                    st.success(f'"{res.specific_language}"')
                else:
                    st.warning("No resolution attempted")
            with c3:
                st.markdown("**Result**")
                if out.resolved:
                    st.success("Resolved")
                else:
                    st.error("Unresolved")
                if out.next_action:
                    st.caption(f"Next: {out.next_action}")
                st.progress(triple.confidence, text=f"Confidence: {triple.confidence:.0%}")

    # Buying Intent Markers
    st.subheader("Buying Intent Markers")
    st.caption(
        "Linguistic cues that correlate with deal progression. 'If' to 'when' "
        "shifts signal the prospect is mentally past evaluation."
    )
    if behavioral.buying_intent_markers:
        for marker in behavioral.buying_intent_markers:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**{_fmt(marker.type)}**")
                    st.caption(f"Confidence: {marker.confidence:.0%}")
                with col2:
                    st.markdown(f'"{marker.evidence}"')

    # Competitive Mentions
    if behavioral.competitive_mentions:
        st.subheader("Competitive Mentions")
        data = [
            {
                "Competitor": cm.competitor,
                "Context": cm.context,
                "Sentiment": cm.sentiment.title(),
                "Comparison": cm.comparison_type or "",
            }
            for cm in behavioral.competitive_mentions
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    # Engagement Trajectory
    st.subheader("Engagement Trajectory")
    st.caption("How the prospect's engagement evolved through the conversation.")
    if behavioral.engagement_trajectory:
        cols = st.columns(len(behavioral.engagement_trajectory))
        for col, point in zip(cols, behavioral.engagement_trajectory):
            with col:
                st.markdown(f"**{_fmt(point.phase)}**")
                st.markdown(f"Participation: {_fmt(point.participation_level)}")
                st.markdown(f"Question depth: {_fmt(point.question_depth)}")
                st.markdown(f"Energy: {_fmt(point.energy)}")
                if point.notes:
                    st.caption(point.notes)


# ---------------------------------------------------------------------------
# Tab: Psychographic Profile
# ---------------------------------------------------------------------------

def render_psychographic(psychographic: PsychographicSignals) -> None:
    # Mental Model
    st.subheader("Buyer Mental Model")
    st.caption(
        "The evaluation lens the buyer uses to make decisions. Mismatched messaging kills deals."
    )
    mm = psychographic.mental_model
    st.markdown(f"**Primary:** {_fmt(mm.primary)}")
    if mm.secondary:
        st.markdown(f"**Secondary:** {_fmt(mm.secondary)}")
    st.markdown(f"**Confidence:** {mm.confidence:.0%}")
    with st.expander("Reasoning & Evidence"):
        st.markdown(mm.reasoning)
        for e in mm.evidence:
            st.markdown(f"- {e}")

    # Persona Indicators
    st.subheader("Persona Indicators")
    st.caption(
        "Persona identification tells content teams which messaging style will resonate."
    )
    if psychographic.persona_indicators:
        data = [
            {
                "Archetype": _fmt(p.archetype),
                "Confidence": p.confidence,
            }
            for p in psychographic.persona_indicators
        ]
        fig = px.bar(
            data,
            x="Confidence",
            y="Archetype",
            orientation="h",
            color="Confidence",
            color_continuous_scale=["#fee2e2", "#22c55e"],
            range_x=[0, 1],
        )
        fig.update_layout(height=200, showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        for p in psychographic.persona_indicators:
            with st.expander(f"{_fmt(p.archetype)} ({p.confidence:.0%})"):
                st.markdown(p.reasoning)
                for e in p.evidence:
                    st.markdown(f"- {e}")

    # Language Fingerprint
    st.subheader("Language Fingerprint")
    st.caption(
        "The prospect's own vocabulary. Content that mirrors these words and "
        "framing patterns will feel personalized and trustworthy."
    )
    lf = psychographic.language_fingerprint
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Distinctive Vocabulary**")
        for v in lf.distinctive_vocabulary:
            st.markdown(f"- `{v}`")
    with c2:
        st.markdown("**Metaphors**")
        for m in lf.metaphors:
            st.markdown(f"- *{m}*")
    with c3:
        st.markdown("**Framing Patterns**")
        for f in lf.framing_patterns:
            st.markdown(f"- {f}")


# ---------------------------------------------------------------------------
# Tab: Multimodal Analysis
# ---------------------------------------------------------------------------

def render_multimodal(
    multimodal: MultimodalSignals | None,
    transcript: Transcript,
) -> None:
    if multimodal is None:
        st.info(
            "No paralinguistic annotations available for this transcript. "
            "Multimodal analysis requires audio/video cues (pauses, pitch, energy, behaviors)."
        )
        return

    utterance_map = {u.turn_index: u for u in transcript.utterances}

    # Divergence Signals
    st.subheader("Text-Audio Divergences")
    st.caption(
        "When someone says 'that sounds great' while shifting in their seat and "
        "avoiding eye contact, the words are misleading. Multimodal analysis catches "
        "these hidden signals."
    )
    for d in multimodal.divergences:
        u = utterance_map.get(d.utterance_index)
        with st.container(border=True):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Turn {d.utterance_index}** &mdash; {_fmt(d.type)}")
                if u:
                    st.markdown(f'> "{u.text}"')
                st.caption(f"Text sentiment: {d.text_sentiment} | Confidence: {d.confidence:.0%}")
            with c2:
                st.markdown("**Non-verbal Cues**")
                for cue in d.nonverbal_cues:
                    st.markdown(f"- {cue}")
                st.markdown(f"**Interpretation:** {d.interpretation}")

    # Composite Sentiments
    if multimodal.composite_sentiments:
        st.subheader("Adjusted Sentiments")
        st.caption("Sentiment scores adjusted after multimodal signal fusion.")
        data = [
            {
                "Turn": cs.utterance_index,
                "Original": cs.original_text_polarity.title(),
                "Adjusted": cs.adjusted_polarity.title(),
                "Confidence": f"{cs.confidence:.0%}",
                "Note": cs.note or "",
            }
            for cs in multimodal.composite_sentiments
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
