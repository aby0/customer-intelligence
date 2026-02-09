"""Home page for the Customer Intelligence demo."""

from __future__ import annotations

import streamlit as st

st.title("Customer Intelligence Pipeline")
st.markdown(
    "An AI-powered pipeline that extracts deep, actionable signals from "
    "**sales call transcripts** — from surface sentiment to behavioral patterns "
    "to psychographic traits."
)

st.divider()

# --- The Problem ---
st.subheader("The Problem")
st.markdown(
    "A 45-minute sales call produces ~8,000 words of unstructured dialogue. "
    "Marketers can't use it. Sales reps summarize it badly. CRMs capture none "
    "of the nuance. The result: marketing content is written in a vacuum, "
    "disconnected from what customers actually said, felt, and cared about."
)
st.markdown(
    "**The real question isn't \"what did the customer say?\" — it's "
    "\"what does it reveal about how they think, what they'll do next, "
    "and how we should talk to them?\"**"
)

st.divider()

# --- The Intelligence Stack ---
st.subheader("The Three-Layer Intelligence Stack")
st.markdown(
    "We extract customer signals at three depths, each more valuable than the last:"
)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**Layer 1: Surface Signals**")
        st.caption("Table stakes — necessary but not differentiating")
        st.markdown(
            "- Aspect-based sentiment\n"
            "- Topic detection\n"
            "- Named entities\n"
            "- Key phrases"
        )

with col2:
    with st.container(border=True):
        st.markdown("**Layer 2: Behavioral Signals**")
        st.caption("Conversation dynamics — where it gets interesting")
        st.markdown(
            "- Objection-resolution-outcome triples\n"
            "- Buying intent markers\n"
            "- Competitive positioning\n"
            "- Engagement trajectory"
        )

with col3:
    with st.container(border=True):
        st.markdown("**Layer 3: Psychographic Signals**")
        st.caption("Customer psychology — the hard problem")
        st.markdown(
            "- Buyer mental model\n"
            "- Behavioral persona indicators\n"
            "- Language fingerprint"
        )

st.divider()

# --- Multimodal ---
st.subheader("Multimodal Divergence Detection")
st.markdown(
    "When paralinguistic annotations are available (pauses, pitch, energy, "
    "hesitation markers), the pipeline detects contradictions between what "
    "the customer *says* and *how they say it*. Hidden objections — like "
    'saying "pricing looks reasonable" with a 2-second pause and dropping '
    "pitch — surface explicitly rather than being masked."
)

st.divider()

# --- Navigation ---
st.subheader("Explore")
st.markdown(
    "- **Pipeline Demo** — See signal extraction in action on real sales calls\n"
    "- **Documentation** — Technical docs on approach, evaluation, and roadmap"
)
