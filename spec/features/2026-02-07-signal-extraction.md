# Feature: Multi-Layer Signal Extraction (Module 1)

**Date**: 2026-02-07
**Status**: WIP
**Last updated**: 2026-02-07

## User Value

A sales call transcript is dense with signal — but it's buried in conversational noise. Marketers can't read hundreds of calls to find the three quotes that matter. Sales leaders can't manually track which objection-handling approaches actually work. This module transforms a raw transcript into structured, queryable intelligence: what aspects the customer cares about, what objections they raised and how those were handled, what kind of buyer they are, and where their words contradict their tone.

## How It Works

The extraction pipeline processes a single sales call transcript and produces a structured JSON document containing signals organized into three layers of increasing depth.

### Layer 1: Surface Signals

These are well-understood NLP extractions that provide the foundation:

- **Aspect-based sentiment**: Instead of a single sentiment score per utterance, the system identifies *what aspect* the sentiment is about and scores it independently. "I love the product but the pricing feels steep" yields `product: positive (0.8)` and `pricing: negative (0.6)` with context ("company size concern").
- **Topic detection**: What subjects are discussed and when they appear in the conversation timeline.
- **Named entities**: People, products, companies, and competitors mentioned, with role attribution where possible.
- **Key phrases**: Important terms and concepts weighted by relevance to the sales context.

### Layer 2: Behavioral Signals

These require understanding conversation *dynamics* — sequences, turn-taking, and evolution over time:

- **Objection-Resolution-Outcome triples**: When a prospect raises a concern, the system extracts the objection (type, specific language, speaker role, conversation stage), the resolution attempted by the sales rep (type, specific language), and the observed outcome (resolved/unresolved, deal progressed, next action). This is the core data asset for building data-driven content playbooks.
- **Buying intent markers**: Linguistic shifts that correlate with deal progression — "if" to "when" transitions, timeline questions, stakeholder introductions, implementation detail requests.
- **Decision-maker mapping**: Who speaks, who asks questions, whose concerns dominate, who defers to whom. Inferred from turn-taking patterns and question types.
- **Competitive positioning**: How competitors are mentioned — in what context, with what sentiment, as alternatives or as incumbent, with what specific comparisons.
- **Engagement trajectory**: How the prospect's participation depth, question quality, and response energy change across the conversation.

### Layer 3: Psychographic Signals

These are meta-features about customer *psychology* — the hardest to extract and the most valuable:

- **Buyer mental model**: What evaluation framework is the prospect using? Cost-reduction ("save money"), growth-enablement ("scale faster"), risk-mitigation ("reduce exposure"), efficiency ("save time"). Determines content framing.
- **Language fingerprint**: The specific vocabulary, metaphors, and framing the customer uses. Enables content that mirrors their voice.
- **Behavioral persona indicators**: Patterns suggesting which buyer archetype they match — Analytical Evaluator (asks technical questions, wants data), Executive Champion (strategic focus, wants social proof), Reluctant Adopter (risk-averse, needs reassurance).

### Multimodal Divergence Detection

When paralinguistic annotations are present in the transcript (pauses, hesitation markers, energy levels, pitch indicators), the system detects divergence between text sentiment and non-verbal cues:

- Text says "pricing looks reasonable" + 2.3s pause + falling pitch + low energy = flagged as "likely hidden pricing concern"
- Text says "let me discuss with my team" + quick speech + high energy = flagged as "genuine buying signal — prospect will advocate internally"

The system computes a composite sentiment score using weighted fusion (text: 0.4, audio: 0.35, video: 0.25) and adjusts confidence when divergence is detected.

## Key Interactions

- **When processing a transcript without paralinguistic annotations**: Layers 1-3 extract normally. Multimodal divergence detection is skipped. Composite sentiment defaults to text-only scores with a note that non-verbal signals were unavailable.
- **When an objection is detected but no resolution follows**: The triple is recorded with `resolution_attempted: null` and `outcome: "unresolved"`. These unresolved objections are high-priority signals for content strategy.
- **When the same aspect appears with contradictory sentiment across utterances**: Both are captured with timestamps. The trajectory (positive-then-negative vs. negative-then-positive) is itself a signal — sentiment reversal patterns are flagged.
- **When speaker roles can't be determined**: The system defaults to a two-speaker model (rep vs. prospect) based on conversation patterns (who asks discovery questions = rep, who describes their situation = prospect). Low-confidence attributions are flagged.
- **When the transcript is very short (< 10 turns)**: Layer 3 extractions (persona, mental model) are marked as low-confidence since there isn't enough signal for reliable psychographic inference.
- **Edge case — multiple prospects on the call**: The system attempts per-speaker signal extraction. Decision-maker mapping becomes especially important — extract who speaks most, who asks the hardest questions, who has final-say language patterns.

## Acceptance Criteria

### Schema & Structure
- [ ] Output conforms to a defined JSON schema with all three signal layers
- [ ] Every extracted signal includes a confidence score (0-1) and provenance (source utterance references)
- [ ] Schema is documented and validates against sample outputs

### Layer 1 — Surface Signals
- [ ] Aspect-based sentiment identifies distinct aspects within a single utterance (e.g., product vs. pricing) with per-aspect polarity and intensity
- [ ] Topic detection identifies the primary topics discussed with approximate conversation-timeline positioning
- [ ] Named entities are extracted with type labels (person, company, product, competitor)

### Layer 2 — Behavioral Signals
- [ ] Objections are extracted as structured triples: objection (type + specific language + speaker role + stage), resolution attempted (type + specific language), outcome (resolved/unresolved + deal impact)
- [ ] Buying intent markers are identified with type classification (timeline question, stakeholder introduction, "if→when" shift, implementation detail request)
- [ ] Competitive mentions are extracted with context and sentiment
- [ ] Engagement trajectory captures how prospect participation evolves across the conversation

### Layer 3 — Psychographic Signals
- [ ] Buyer mental model is classified into at least one of: cost-reduction, growth-enablement, risk-mitigation, efficiency — with supporting evidence from the transcript
- [ ] Behavioral persona indicators are extracted with confidence scores, mapping to archetypes (Analytical Evaluator, Executive Champion, Reluctant Adopter, or other emergent types)
- [ ] Language fingerprint captures distinctive vocabulary and framing patterns used by the prospect

### Multimodal
- [ ] When paralinguistic annotations are present, text-audio divergence is detected and flagged
- [ ] Composite sentiment adjusts confidence when divergence exceeds a threshold
- [ ] System gracefully degrades when no paralinguistic annotations are available (text-only mode)

### Evaluation
- [ ] Extraction quality is evaluated against a human-annotated golden set (at least 3 transcripts)
- [ ] Evaluation covers precision and recall for each signal type independently

## Related Features

- [Pipeline Architecture](2026-02-07-pipeline-architecture.md) — defines where this module sits in the overall system
- [Synthetic Data Generation](2026-02-07-synthetic-data-generation.md) — provides the test transcripts this module processes

## Design Decisions

- **Why LLM extraction with chain-of-thought?** Psychographic signals (Layer 3) require *reasoning* about customer psychology, not just pattern matching. Chain-of-thought prompting lets the LLM show its work — "the prospect asked three detailed technical questions before any pricing discussion, suggesting an Analytical Evaluator persona." This reasoning is part of the provenance record.
- **Why structured output schemas?** Enforcing typed schemas (via function calling or structured output mode) ensures consistent, parseable output across all transcripts. Without schema enforcement, LLM extraction drifts in format and completeness.
- **Why aspect-based over utterance-level sentiment?** A single utterance often contains mixed sentiment about different aspects. Utterance-level sentiment averages these away. Aspect-level granularity is what makes the output actionable — "likes the product, concerned about pricing" drives specific content choices.
- **Why simulated multimodal for POC?** Real audio processing (librosa, Whisper) adds engineering complexity without testing the core hypothesis: does multimodal divergence detection surface useful signals? Simulated annotations let us validate the detection logic and schema before investing in audio pipeline engineering.

## Notes

- The extraction uses a schema-first approach: define the exact output structure, then write prompts that fill it
- For the POC, extraction is single-pass (one LLM call per transcript per layer) — production might use multi-pass with specialized prompts per signal type
- The objection-resolution-outcome triples are the most valuable output for Module 2's pattern mining
- Persona classification uses a soft assignment (confidence scores per archetype) rather than hard labels, since real buyers blend characteristics
