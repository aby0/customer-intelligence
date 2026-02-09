"""Page 1: Interactive pipeline demo — explore signal extraction from sales calls."""

from __future__ import annotations

import streamlit as st

from customer_intelligence.demo.components import (
    render_behavioral,
    render_conversation,
    render_multimodal,
    render_pipeline_overview,
    render_psychographic,
    render_summary,
    render_surface,
)
from customer_intelligence.demo.data_loader import (
    get_display_label,
    has_paralinguistic,
    load_extractions,
    load_summaries,
    load_transcripts,
)
from customer_intelligence.demo.insights import (
    generate_content_recommendations,
    generate_key_findings,
    generate_risk_flags,
)

# Load data
transcripts = load_transcripts()
extractions = load_extractions()
summaries = load_summaries()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Customer Intelligence")
    st.caption("AI-powered signal extraction from sales calls")
    st.divider()

    # Build dropdown options
    options: dict[str, str] = {}
    for call_id, t in transcripts.items():
        options[get_display_label(t)] = call_id

    selected_label = st.selectbox("Select a sales call", list(options.keys()))
    call_id = options[selected_label]  # type: ignore[index]
    transcript = transcripts[call_id]
    extraction = extractions.get(call_id)
    summary = summaries.get(call_id)

    # Metadata
    st.divider()
    a = transcript.account
    st.markdown(f"### {a.company_name}")
    c1, c2 = st.columns(2)
    c1.metric("Stage", a.deal_stage.replace("_", " ").title())
    c2.metric("Outcome", a.deal_outcome.upper())

    c3, c4 = st.columns(2)
    c3.metric("Size", a.company_size.replace("_", "-"))
    c4.metric("Duration", f"{transcript.call_metadata.duration_minutes}m")

    st.caption(f"Industry: {a.industry}")
    st.caption(f"Turns: {len(transcript.utterances)}")
    st.caption(f"Paralinguistic: {'Yes' if has_paralinguistic(transcript) else 'No'}")

    if extraction:
        st.divider()
        st.metric("Pipeline Confidence", f"{extraction.overall_confidence:.0%}")
        c5, c6 = st.columns(2)
        c5.metric("Objections", len(extraction.behavioral.objection_triples))
        c6.metric("Intent Markers", len(extraction.behavioral.buying_intent_markers))

    # Stakeholders
    st.divider()
    st.markdown("**Stakeholders**")
    for s in a.stakeholders:
        st.caption(f"{s.name} ({s.role}) — {s.persona_type.replace('_', ' ').title()}")


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

if extraction is None and summary is None:
    st.warning(
        f"No extraction or summary data available for **{call_id}**. "
        "Showing transcript only."
    )
    render_conversation(transcript)
else:
    tab_names = ["Pipeline Overview", "Call Summary", "Conversation", "Surface Signals",
                 "Behavioral Signals", "Psychographic Profile", "Multimodal Analysis",
                 "Actionable Insights"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_pipeline_overview(extraction, transcript)

    with tabs[1]:
        if summary:
            render_summary(summary)
        else:
            st.info("No summary available for this call. Run `generate_summaries.py` to generate.")

    with tabs[2]:
        render_conversation(transcript)

    with tabs[3]:
        if extraction:
            render_surface(extraction.surface)
        else:
            st.info("No extraction data available.")

    with tabs[4]:
        if extraction:
            render_behavioral(extraction.behavioral, transcript)
        else:
            st.info("No extraction data available.")

    with tabs[5]:
        if extraction:
            render_psychographic(extraction.psychographic)
        else:
            st.info("No extraction data available.")

    with tabs[6]:
        if extraction:
            render_multimodal(extraction.multimodal, transcript)
        else:
            st.info("No extraction data available.")

    with tabs[7]:
        if extraction:
            st.subheader("Key Findings")
            for finding in generate_key_findings(extraction):
                st.markdown(f"- {finding}")

            st.subheader("Content Recommendations")
            for rec in generate_content_recommendations(extraction):
                st.markdown(f"- {rec}")

            risk_flags = generate_risk_flags(extraction)
            if risk_flags:
                st.subheader("Risk Flags")
                for flag in risk_flags:
                    st.markdown(f"- {flag}")
            else:
                st.subheader("Risk Flags")
                st.success("No significant risk flags detected.")

            if extraction.notes:
                st.subheader("Notes")
                for note in extraction.notes:
                    st.caption(note)
        else:
            st.info("No extraction data available.")
