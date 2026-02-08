# Feature: Synthetic Sales Call Data Generation

**Date**: 2026-02-07
**Status**: WIP
**Last updated**: 2026-02-07

## User Value

The pipeline needs realistic sales call transcripts to develop and validate against — but we don't have access to real Gong recordings. Synthetic data generation creates a controlled, annotated dataset that exercises every extraction capability: different buyer personas, deal stages, objection types, multi-call account threads, and paralinguistic annotations. Well-designed synthetic data also forces us to think carefully about what "realistic" sales call data looks like, which is domain understanding the team needs regardless.

## How It Works

The data generator produces a corpus of sales call transcripts representing multiple accounts at different stages of the B2B sales journey. Each transcript is a realistic, multi-turn conversation between a sales rep and one or more prospects, with embedded signals at all three intelligence layers.

### Account Profiles

Each synthetic account has a defined profile that governs the conversations:
- **Company**: name, size, industry vertical
- **Deal stage**: discovery, evaluation, negotiation, close, or lost
- **Deal outcome**: won, lost, or stalled (known but not visible in transcript — used for pattern mining validation)
- **Stakeholders**: roles (VP Marketing, CFO, technical lead), each with a persona type and specific concerns

### Transcript Structure

Each transcript follows realistic sales call structure:
- Speaker-labeled turns with natural conversational flow (not Q&A format)
- Realistic objections with varied resolution approaches
- Buying signals embedded at appropriate stages
- Competitive mentions where contextually appropriate
- Natural topic transitions and tangents

### Paralinguistic Annotations

Transcripts include inline annotations simulating audio/video signals:
- `[2.1s pause]` — silence before response
- `[hesitant]`, `[confident]`, `[enthusiastic]` — energy/tone markers
- `[energy: LOW]`, `[pitch: FALLING]` — prosodic feature indicators
- `[INTERRUPTS]` — turn-taking dynamics
- `[lean_forward]`, `[note_taking]` — video behavior indicators (where applicable)

These annotations are placed to create deliberate text-audio divergence scenarios (e.g., positive words with `[hesitant]` and `[energy: LOW]` to simulate hidden objections).

### Multi-Call Threads

Some accounts have multiple conversations over time, showing:
- Engagement trajectory changes (warming, cooling, recovering)
- Objection evolution (raised → addressed → resolved, or raised → unaddressed → deal stalls)
- Stakeholder expansion (new participants join later calls)
- Stage progression across conversations

### Ground Truth Annotations

Each transcript includes a companion annotation file with the expected extraction output — the "golden set" for evaluation:
- All signals that should be extracted at each layer
- Correct objection-resolution-outcome triples
- Expected persona classifications
- Flagged divergence points
- Deal outcome label

## Key Interactions

- **When generating a new account**: The generator creates a consistent profile first (company, stakeholders, deal trajectory), then generates conversations that are coherent with that profile. A "reluctant adopter" CFO at an enterprise company speaks differently from an "executive champion" VP at a startup.
- **When creating multi-call threads**: Later calls reference earlier ones naturally ("As we discussed last week...") and show realistic evolution — objections from call 1 may be addressed in call 2, new concerns may emerge.
- **When embedding paralinguistic annotations**: Annotations are placed to create a mix of congruent signals (positive text + high energy = genuine enthusiasm) and divergent signals (positive text + low energy = hidden concern). The ratio should favor congruent (~70%) to match real-world distribution.
- **Edge case — very short calls**: Include at least one 5-minute "quick check-in" call to test the pipeline's behavior on minimal data.
- **Edge case — multi-stakeholder calls**: Include at least one call with 3+ participants to test speaker attribution and decision-maker mapping.

## Acceptance Criteria

### Corpus Coverage
- [ ] At least 5 distinct accounts with different company profiles (size, industry)
- [ ] At least 3 deal outcomes represented: won, lost, and stalled
- [ ] At least 3 buyer persona types represented across stakeholders: Analytical Evaluator, Executive Champion, Reluctant Adopter
- [ ] At least 4 deal stages covered: discovery, evaluation, negotiation, close
- [ ] At least 2 accounts have multi-call threads (2+ conversations over time)

### Transcript Quality
- [ ] Each transcript has speaker-labeled turns with natural conversational flow
- [ ] At least 3 distinct objection types appear across the corpus (pricing, implementation, competition, risk, timeline)
- [ ] Buying intent markers are embedded in evaluation/negotiation stage transcripts
- [ ] Competitive mentions appear in at least 2 transcripts
- [ ] Transcripts vary in length (short: ~15 turns, medium: ~30 turns, long: ~50+ turns)

### Paralinguistic Annotations
- [ ] At least 3 transcripts include paralinguistic annotations
- [ ] Annotations create at least 3 text-audio divergence scenarios (positive text with negative non-verbal cues)
- [ ] At least 2 transcripts have no paralinguistic annotations (to test graceful degradation)

### Ground Truth
- [ ] Each transcript has a companion ground truth file with expected extraction output
- [ ] Ground truth covers all three signal layers (surface, behavioral, psychographic)
- [ ] Ground truth includes expected objection-resolution-outcome triples
- [ ] Ground truth includes expected persona classifications with rationale

## Related Features

- [Signal Extraction (Module 1)](2026-02-07-signal-extraction.md) — consumes these transcripts as input
- [Pipeline Architecture](2026-02-07-pipeline-architecture.md) — defines the overall system context

## Design Decisions

- **Why LLM-generated synthetic data over hand-written?** LLMs can generate varied, realistic conversations faster than manual authoring. However, the ground truth annotations should be human-reviewed to ensure accuracy — the LLM generates the conversations, a human validates the expected extractions.
- **Why include ground truth annotations?** Without known-correct extraction targets, we can't evaluate Module 1's accuracy. The golden set enables precision/recall measurement for each signal type.
- **Why paralinguistic annotations in text form?** Real audio processing (librosa, Whisper) is out of POC scope. Text annotations simulate multimodal signals with zero infrastructure overhead while validating the divergence detection logic. The schema is designed so swapping in real audio features requires changing the ingestion layer, not the detection logic.
- **Why emphasize multi-call threads?** Module 2 (Pattern Mining) requires temporal data across conversations. Without multi-call threads in the synthetic data, we can't validate temporal pattern extraction even conceptually.

## Notes

- The synthetic data generation itself is a valuable interview artifact — it demonstrates domain understanding of B2B sales conversations
- Consider using a structured generation approach: define the account profile → generate a conversation outline → expand to full transcript → add paralinguistic annotations → create ground truth
- The corpus should be small enough to review manually but large enough to exercise the extraction pipeline meaningfully
- Ground truth annotation is the bottleneck — budget time for careful human review of expected outputs
