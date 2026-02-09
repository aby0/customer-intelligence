# Pipeline Workflow

End-to-end guide: generate synthetic data, extract signals, validate results.

## 1. Generate Synthetic Corpus

```bash
python -m customer_intelligence.synthetic.generator
```

This iterates through account profiles defined in `src/customer_intelligence/synthetic/profiles.py` (5 accounts, 7 total calls). For each call it makes two LLM requests:

1. **Generate transcript** -- builds a prompt from the account profile (company, stakeholders, deal stage, objection types) and asks Claude to produce a realistic sales call transcript.
2. **Generate ground truth** -- takes the transcript and asks Claude to annotate every signal across all extraction layers.

Output:
- `data/transcripts/{call_id}.json` -- Transcript objects
- `data/ground_truth/{call_id}.json` -- ExtractionResult objects (gold labels)

Re-running skips pairs where both files already exist. If a transcript exists but its ground truth doesn't, it reloads the transcript from disk and only regenerates the ground truth.

### Current corpus

| Account | Calls | Outcome | Paralinguistic |
|---------|-------|---------|----------------|
| TechCorp | 1 | won | yes |
| GrowthCo | 1 | won | no |
| SafeGuard Inc | 1 | stalled | yes |
| ScaleUp Ltd | 2 | won | yes |
| Legacy Systems Corp | 2 | lost | no |

For profile definitions and design rationale, see the [synthetic data spec](../spec/features/2026-02-07-synthetic-data-generation.md).

## 2. Extract Signals

```bash
python -m customer_intelligence.extraction.extractor data/transcripts/techcorp_call1.json
```

Runs the four-layer extraction pipeline on a single transcript and prints the ExtractionResult JSON to stdout.

**Layers:**

| Layer | Signals | Always runs? |
|-------|---------|-------------|
| Surface | Aspect sentiment, topics, entities, key phrases | Yes |
| Behavioral | Objection triples, buying intent, competitive mentions, engagement trajectory | Yes |
| Psychographic | Mental model, persona indicators, language fingerprint | Yes |
| Multimodal | Text-audio divergences, composite sentiments | Only if transcript has paralinguistic annotations |

Short transcripts (<10 turns) get a note flagging low psychographic confidence.

To save results to a file:

```bash
python -m customer_intelligence.extraction.extractor data/transcripts/techcorp_call1.json > results.json
```

For signal definitions and schema details, see the [signal extraction spec](../spec/features/2026-02-07-signal-extraction.md).

## 3. Validate

Three test suites, ordered from fast/offline to slow/online:

### Schema tests (no LLM)

```bash
pytest tests/test_schemas.py -v
```

Validates Pydantic models: required fields, constraints (0-1 float ranges, enum values), roundtrip serialization.

### Corpus coverage tests (no LLM)

```bash
pytest tests/test_synthetic.py -v
```

Validates the generated corpus meets spec acceptance criteria:
- 5+ unique accounts, 3+ deal outcomes, 3+ persona types
- Multi-call threads, paralinguistic coverage
- Ground truth completeness (all layers present)
- 3+ objection types across the corpus

Requires `data/` to be populated (Step 1).

### Integration tests (uses LLM)

```bash
pytest tests/test_extraction.py -m integration -v
```

Runs extraction on each transcript and compares against ground truth:

| What's tested | Threshold |
|--------------|-----------|
| Topic detection recall | >= 50% |
| Entity detection recall | >= 50% |
| Objection type recall | >= 50% |
| Buying intent presence | If GT has markers, extraction should too |
| Primary mental model match | >= 50% accuracy |
| Persona archetype overlap | At least one match |
| Multimodal divergence detection | Present when GT has divergences |

Requires `data/` to be populated (Step 1) and `ANTHROPIC_API_KEY`.

## 4. Run Everything

```bash
# Generate corpus (skip if data/ already populated)
python -m customer_intelligence.synthetic.generator

# Run all tests
pytest tests/ -v
```
