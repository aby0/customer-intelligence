"""Synthesize actionable insights from extraction data (no LLM calls)."""

from __future__ import annotations

from customer_intelligence.schemas.extraction import ExtractionResult


def generate_key_findings(extraction: ExtractionResult) -> list[str]:
    """Generate top key findings from extraction data."""
    findings: list[str] = []

    # Mental model insight
    mm = extraction.psychographic.mental_model
    finding = f"Buyer evaluates through a **{mm.primary.replace('_', ' ')}** lens"
    if mm.secondary:
        finding += f" with secondary focus on **{mm.secondary.replace('_', ' ')}**"
    finding += f" ({mm.confidence:.0%} confidence)"
    findings.append(finding)

    # Objection resolution rate
    triples = extraction.behavioral.objection_triples
    if triples:
        resolved = sum(1 for t in triples if t.outcome.resolved)
        findings.append(
            f"**{resolved} of {len(triples)}** objections resolved "
            f"({resolved / len(triples):.0%} resolution rate)"
        )
        # Most common objection type
        type_counts: dict[str, int] = {}
        for t in triples:
            type_counts[t.objection.type] = type_counts.get(t.objection.type, 0) + 1
        top_type = max(type_counts, key=type_counts.get)  # type: ignore[arg-type]
        findings.append(
            f"Most common objection type: **{top_type.replace('_', ' ')}** "
            f"({type_counts[top_type]} occurrences)"
        )

    # Buying intent strength
    markers = extraction.behavioral.buying_intent_markers
    if markers:
        avg_conf = sum(m.confidence for m in markers) / len(markers)
        findings.append(
            f"**{len(markers)}** buying intent markers detected "
            f"(avg confidence: {avg_conf:.0%})"
        )

    # Persona
    personas = extraction.psychographic.persona_indicators
    if personas:
        top_persona = max(personas, key=lambda p: p.confidence)
        findings.append(
            f"Primary persona: **{top_persona.archetype.replace('_', ' ').title()}** "
            f"({top_persona.confidence:.0%} confidence)"
        )

    return findings


def generate_content_recommendations(extraction: ExtractionResult) -> list[str]:
    """Generate content recommendations based on persona and mental model."""
    recs: list[str] = []

    mm = extraction.psychographic.mental_model
    model_recs = {
        "cost_reduction": "Lead with ROI calculators, cost-comparison tables, and savings projections.",
        "growth_enablement": "Lead with growth metrics, scale stories, and expansion use cases.",
        "risk_mitigation": "Lead with security guarantees, compliance certifications, and risk assessments.",
        "efficiency": "Lead with time-savings data, workflow improvements, and automation examples.",
    }
    if mm.primary in model_recs:
        recs.append(model_recs[mm.primary])

    personas = extraction.psychographic.persona_indicators
    if personas:
        top = max(personas, key=lambda p: p.confidence)
        persona_recs = {
            "analytical_evaluator": "Provide detailed data sheets, technical documentation, and benchmark comparisons.",
            "executive_champion": "Provide strategic narratives, executive summaries, and social proof from peer companies.",
            "reluctant_adopter": "Provide implementation guides, support SLAs, and migration risk mitigation plans.",
        }
        if top.archetype in persona_recs:
            recs.append(persona_recs[top.archetype])

    # Language fingerprint
    lf = extraction.psychographic.language_fingerprint
    if lf.distinctive_vocabulary:
        sample = ", ".join(f'"{w}"' for w in lf.distinctive_vocabulary[:4])
        recs.append(f"Mirror the prospect's vocabulary in content: {sample}.")

    return recs


def generate_risk_flags(extraction: ExtractionResult) -> list[str]:
    """Identify risk signals from the extraction."""
    flags: list[str] = []

    # Unresolved objections
    unresolved = [
        t for t in extraction.behavioral.objection_triples if not t.outcome.resolved
    ]
    if unresolved:
        types = ", ".join(_fmt(t.objection.type) for t in unresolved)
        flags.append(f"**{len(unresolved)}** unresolved objection(s): {types}")

    # Declining engagement
    trajectory = extraction.behavioral.engagement_trajectory
    if len(trajectory) >= 2:
        energy_order = {"low": 0, "medium": 1, "high": 2}
        last = trajectory[-1]
        first = trajectory[0]
        if energy_order.get(last.energy, 1) < energy_order.get(first.energy, 1):
            flags.append("Engagement energy **declined** from start to end of call")

    # Multimodal divergences
    if extraction.multimodal and extraction.multimodal.divergences:
        neg_divs = [
            d for d in extraction.multimodal.divergences
            if "negative" in d.type
        ]
        if neg_divs:
            flags.append(
                f"**{len(neg_divs)}** text-audio divergence(s) with hidden negative sentiment detected"
            )

    return flags


def _fmt(text: str) -> str:
    return text.replace("_", " ")
