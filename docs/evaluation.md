# Evaluation Pipeline

How we measure extraction quality — what we evaluate, why, and how.

## Why Three Methods

Signal extraction is a mix of objective and subjective tasks. Named entity extraction has clear right/wrong answers; aspect granularity ("pricing" vs "cost" vs "the 185K annual license pricing") is a judgment call. No single evaluation method covers both well.

We use three complementary approaches:

| Method | Measures | Cost | Deterministic |
|--------|----------|------|---------------|
| **Programmatic metrics** | Precision, recall, F1 via fuzzy matching against ground truth | Free | Yes |
| **LLM-as-judge** | Subjective quality — granularity, reasoning, interpretation | ~$0.01/signal | No |
| **NLP baselines** | Cross-validation — do traditional tools agree with LLM extraction? | Free (after install) | Yes |

**Programmatic metrics** are the primary measure. They run on every evaluation, require no API calls, and directly satisfy the spec acceptance criteria (precision + recall per signal type). LLM-as-judge and NLP baselines are supplementary — they provide richer signal for prompt tuning but are optional at test time.

## Per-Signal Evaluation Matrix

Which method applies where:

| Signal | Programmatic | LLM-as-Judge | NLP Baseline |
|--------|-------------|--------------|-------------|
| Aspect sentiment | P/R on aspects, polarity agreement, intensity MAE | Aspect granularity quality | Sentiment polarity (TextBlob) |
| Topics | P/R on topic names, timeline accuracy | — | — |
| Named entities | P/R on names, entity type accuracy | — | Entity recall (spaCy NER) |
| Key phrases | P/R on phrases, relevance MAE | — | Phrase overlap (YAKE) |
| Objection triples | P/R on objection types, resolution/outcome accuracy | Triple completeness | — |
| Buying intent | P/R on intent types, count comparison | — | — |
| Competitive mentions | P/R on competitor names, sentiment accuracy | Context quality | — |
| Engagement trajectory | Phase coverage, ordinal agreement | — | — |
| Mental model | Primary/secondary match, confidence delta | Reasoning quality | — |
| Persona indicators | P/R on archetypes, confidence delta | Reasoning quality | — |
| Language fingerprint | Vocabulary overlap, metaphor overlap | Framing pattern quality | — |
| Divergences | P/R on utterance indices, type accuracy | Interpretation quality | — |
| Composite sentiment | P/R on utterance indices, polarity accuracy | — | — |

## Fuzzy Matching

Ground truth says "ROI justification"; extraction says "ROI analysis". Exact string matching fails. We use two tiers:

### Tier 1: Token Overlap (always available)

Jaccard similarity on lowercased word tokens:

```
similarity("ROI justification", "ROI analysis") = |{roi}| / |{roi, justification, analysis}| = 0.33
similarity("pricing", "pricing negotiation") = |{pricing}| / |{pricing, negotiation}| = 0.50
similarity("David Chen", "David Chen") = 1.0
```

### Tier 2: Embedding Similarity (optional)

Cosine similarity via `sentence-transformers` (`all-MiniLM-L6-v2`). Handles semantic equivalence that token overlap misses: "pricing" ↔ "cost", "implementation timeline" ↔ "deployment schedule".

### Matching Algorithm

Greedy 1:1 matching:
1. Compute all-pairs similarity matrix
2. Sort pairs by similarity descending
3. Greedily assign: take highest pair, mark both as used, repeat
4. Only accept pairs above threshold

### Thresholds

| Signal | Threshold | Why |
|--------|-----------|-----|
| Entity names | 0.8 | Names should be near-exact |
| Topic names | 0.5 | Phrased differently across annotators |
| Aspect names | 0.6 | Same concept, different words |
| Key phrases | 0.4 | Often paraphrased |
| Vocabulary | 0.8 | Distinctive words should match closely |
| Metaphors | 0.5 | Can be paraphrased significantly |

## Metric Definitions

### Precision, Recall, F1

Standard definitions, computed after fuzzy matching:

- **Precision** = matched_extracted / total_extracted — "of what we found, how much was correct?"
- **Recall** = matched_ground_truth / total_ground_truth — "of what exists, how much did we find?"
- **F1** = 2 * P * R / (P + R) — harmonic mean

### Mean Absolute Error (MAE)

For numeric scores (intensity, relevance, confidence) on matched pairs:

```
MAE = mean(|extracted_score - ground_truth_score|) for matched pairs
```

### Ordinal Agreement

For ordered categorical fields (participation_level, question_depth, energy):

```
agreement = 1.0 - |scale.index(predicted) - scale.index(actual)| / (len(scale) - 1)
```

Gives 1.0 for exact match, 0.5 for one step off, 0.0 for maximum disagreement.

### Score Distribution Stats

Detects degenerate outputs (all scores = 0.8):

- Mean, standard deviation
- Bucket counts (0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)

## LLM-as-Judge Design

Uses `claude-haiku-4-5-20251001` for cost efficiency. Every judge call follows the same rubric pattern:

```
You are evaluating the quality of a signal extracted from a sales call transcript.

TRANSCRIPT (relevant excerpt):
{excerpt}

EXTRACTED SIGNAL:
{signal_json}

GROUND TRUTH:
{ground_truth_json}

RUBRIC — Score 1 to 5:
5: {excellent_criterion}
4: {good_criterion}
3: {acceptable_criterion}
2: {poor_criterion}
1: {unacceptable_criterion}

Return ONLY: {"score": <1-5>, "justification": "<2-3 sentences>"}
```

### Rubrics

**Aspect Granularity**: Is the aspect at the right level? (5=exact right level, 1=wrong/nonsensical)

**Objection Triple Completeness**: Are all three components accurate with correct source references? (5=all accurate with quotes, 1=objection misidentified)

**Persona Reasoning**: Does evidence support the archetype? (5=specific evidence, acknowledges nuance, 1=contradicts transcript)

**Framing Pattern Quality**: Are patterns specific and actionable for marketers? (5=specific + insightful, 1=wrong)

**Competitive Context Quality**: Does context capture how competitor was mentioned? (5=full nuance, 1=wrong)

**Divergence Interpretation**: Does interpretation synthesize text + nonverbal correctly? (5=correct synthesis + business implications, 1=wrong)

### Cost Management

- Send only relevant utterances (via `source_utterance_indices`), not the full transcript
- Cache results by `(transcript_id, signal_type, signal_hash)` within a run
- `skip_llm_judge=True` flag for fast/cheap evaluation runs

## NLP Baselines

These are **cross-validation reference points**, not primary metrics. They answer: "does our LLM extraction at least cover what a simple NLP tool would find?"

| Baseline | Library | What it measures |
|----------|---------|-----------------|
| Entity recall | spaCy `en_core_web_sm` | Fraction of spaCy-detected entities present in extraction |
| Keyphrase overlap | YAKE | Fraction of YAKE top-k phrases present in extraction |
| Sentiment agreement | TextBlob | Polarity agreement on source utterances |

All baselines are optional — the evaluation module degrades gracefully when libraries aren't installed.

### Dependencies

```toml
# Required: none beyond existing (pydantic, anthropic)
# Optional:
[project.optional-dependencies]
eval = ["spacy>=3.7", "yake>=0.4.8", "textblob>=0.18"]
```

spaCy requires a separate model download: `python -m spacy download en_core_web_sm`

## Running Evaluation

```bash
# Unit tests (no API, no optional deps)
pytest tests/test_evaluation.py -v

# Integration tests (requires ANTHROPIC_API_KEY)
pytest tests/test_evaluation_integration.py -m integration -v

# With NLP baselines (requires eval deps)
pytest tests/test_evaluation.py -m baseline -v

# Full suite including LLM-as-judge (slow, multiple API calls)
pytest tests/test_evaluation_integration.py -m slow -v
```

From Python / notebooks:

```python
from customer_intelligence.evaluation import evaluate, evaluate_corpus

report = evaluate(extracted_result, ground_truth, transcript)
print(report.summary())

corpus_report = evaluate_corpus(pairs)
```
