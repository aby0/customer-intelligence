# Research Plan: Customer Intelligence from Sales Conversations

*Decomposing a vague product instinct into concrete ML problems, hypotheses, and experiments.*

---

## North Star Metric

**Content-to-Progression Rate:** % of intelligence-grounded content actions that lead to deal stage progression within 14 days.

Everything traces back here:

```
Content-to-Progression Rate
  ├── Content Relevance (right concerns addressed?)
  │     ├── Retrieval Precision (right signals surfaced?)
  │     │     └── Extraction Quality (signals correct?)
  │     └── Pattern Validity (patterns real?)
  └── Content Timing (right content for this stage?)
        └── Stage Classification Accuracy
```

---

## Problem Decomposition

Four ML problems, ordered by maturity and dependency:

```
P1: Signal Extraction (Surface + Latent)     ← Foundation. Build first.
  │
  ├── P2: Pattern Mining                      ← Needs P1 + scale (50+ calls)
  ├── P3: Intelligence-Grounded Retrieval     ← Needs P1 quality
  │
  └── P4: Outcome Attribution                 ← Longest horizon
        P4a: Proxy metrics (buildable now)
        P4b: Causal attribution (6mo+ research)
```

Latent feature detection (psychographic signals, text-tone divergence) is Layer 3 within P1 — same pipeline, deeper reasoning — not a separate system. If L3 quality is poor, ship L1+L2 and keep L3 as research.

---

## Data Strategy

| Phase | Data Needed | Who Labels | Timeline |
|-------|-------------|-----------|----------|
| P1 validation | 10 synthetic + 5 real transcripts, golden set annotations | Self + 1 annotator (LLM-assisted) | Week 1-2 |
| P3 retrieval | 20+ extracted JSONs, relevance judgments for 30 queries | Marketer / domain expert | Week 4-5 |
| P2 patterns | 50+ extracted JSONs + deal outcomes | CRM integration (automated) | Week 7+ |
| P4 attribution | 100+ account timelines | CRM + content platform | Month 3+ |

**Labeling reality at a 4-person startup:** LLM-assisted annotation (Opus generates candidates, human corrects — 3-5x faster). Sales rep validation for lightweight signal checking (2 min per call). Inter-annotator agreement (≥2 annotators on ≥20 examples) for any signal type going to production — if kappa < 0.6, the schema is ambiguous.

---

## P1: Signal Extraction

**Input:** Transcript with speaker labels + optional paralinguistic annotations.
**Output:** Structured JSON — typed signals across three layers, each with confidence and source reference.

**Approach:** LLM-based multi-pass extraction. L1 (surface) first, then L2 (behavioral) with L1 context, then L3 (psychographic) with L1+L2 context. Schema-enforced structured output validated with Pydantic.

**Model options:** Full Sonnet for POC. Tiered extraction (Haiku for L1, Sonnet for L2-3) if Haiku quality drops < 5% on surface signals. Fine-tuned smaller model at >1000 calls/day.

### Key Hypotheses

| ID | Hypothesis | Risk | Validation |
|----|-----------|------|------------|
| H1.1 | Surface extraction ≥ 85% P/R | Low | Golden set on 10 transcripts |
| H1.2 | Multi-pass beats single-pass by ≥ 10% on L2-L3 | Medium (2-3x cost) | A/B compare, human judges |
| H1.3 | Schema captures what marketers find useful | **High — wrong schema = everything downstream is wrong** | Show extractions to 3 marketers |
| H1.4 | Text-only hedging/avoidance detection ≥ 60% expert agreement | Medium | 3 annotators on 20 segments |
| H1.5 | Mental model inference matches sales rep assessment ≥ 50% | Medium | Rep survey on 30 calls |

### Experiments

**Exp 1.1 — Baseline quality (Week 1):** 5 synthetic transcripts, golden set, full pipeline. Target: Surface ≥ 85%, Behavioral ≥ 75%, Latent ≥ 60%. Deliverable: error taxonomy (hallucination / omission / misattribution / schema gap).

**Exp 1.2 — Multi-pass vs. single-pass (Week 2):** Same transcripts, both strategies. Decision gate: if delta < 10%, use single-pass.

**Exp 1.3 — Model tier optimization (Week 2):** Haiku (L1) + Sonnet (L2-3) vs. Sonnet for all. Decision gate: if Haiku-for-L1 drops quality < 5%, adopt tiered strategy.

**Exp 1.4 — Prompt stability (Week 1):** Same transcript, 10 runs. Decision gate: if variance > 15%, use temperature=0 or majority-vote.

**Exp 1.5 — Schema utility (Week 3):** Show extracted outputs to 3 marketers. Decision gate: if they can't identify actionable signals, redesign schema before proceeding.

### Evaluation

**Offline:** Golden set P/R per signal type per layer. Schema validity rate (target: 100%). Inter-annotator agreement. Error taxonomy. Latent signal plausibility rating (1-5, target mean ≥ 3.5).

**Online:** Downstream utility (content with vs. without extraction — blind rating). Extraction drift (weekly golden set check, alert if > 5% drop). User correction rate per signal type.

### Failure Modes

| Failure | Degradation Path |
|---------|-----------------|
| L3 (latent) quality poor | Ship L1+L2 only. Latent signals become research track. |
| High hallucination on behavioral | Confidence threshold > 0.7; flag everything below as "needs review" |
| Schema doesn't match marketer needs | Redesign schema through co-design sessions before building more pipeline |
| Extraction too slow (> 60s) | Accept batch for V1; optimize with tiered models for V2 |

---

## P2: Cross-Call Pattern Mining

**Input:** Extracted JSONs from many calls + deal outcomes.
**Output:** Objection-resolution-outcome frequency tables with significance, persona clusters, engagement trajectories.

**Core challenge: small data.** Early customers have tens of calls. The question is: how little data can you work with?

### Key Hypotheses

| ID | Hypothesis | Risk | Validation |
|----|-----------|------|------------|
| H2.1 | Aggregated objection triples are reliable (extraction error < 20%) | **High — garbage in, garbage out** | Manually verify 30 sampled objections from 50+ calls |
| H2.2 | Meaningful patterns emerge from < 100 calls | **High — if min n is 500+, early customers get no value** | Ablation at n=20, 50, 100, 200 |
| H2.3 | Patterns transfer across industries | **Critical for industry-agnostic claim** | Train on industry A, test on industry B |

**Fallback if H2.3 fails:** The extraction *schema* still transfers even if patterns don't. Customers still get value from P1 extraction + P3 retrieval. Per-industry pattern packs become premium features built with design partners per vertical.

### Experiments

**Exp 2.1 — Aggregation quality (Week 7):** Verify 30 random objections from 50+ extracted calls. Gate: if < 80% correct, P1 must improve first.

**Exp 2.2 — Persona clustering (Week 8):** 15-20 behavioral features per prospect, cluster with k-means/HDBSCAN. Evaluate: silhouette ≥ 0.3, expert can name each cluster.

**Exp 2.3 — Minimum viable data (Week 9):** Subsample at n=20, 50, 100, 200. Measure pattern stability and predictive accuracy at each n. Deliverable: "Pattern type X requires minimum n=Y calls."

**Exp 2.4 — Cross-industry transfer (Month 3+):** Train on industry A, predict on industry B. Report which patterns transfer (structural) vs. which don't (domain-specific).

### Evaluation

**Offline:** Pattern significance (only p < 0.05). Cluster quality (silhouette ≥ 0.3 + interpretable descriptions). Minimum n report.

**Online:** Pattern stability month-over-month (churning = noise). Adoption rate by sales/marketing teams.

---

## P3: Intelligence-Grounded Retrieval

**Input:** Content brief (natural language) + optional filters (persona, stage, industry).
**Output:** Ranked list of relevant extracted signals with source attribution.

**Architecture options:** Pure semantic search (simple, loses structure), structured filters + semantic (best precision, more complex), LLM-based selection (handles nuance, doesn't scale). Hybrid is the target.

### Key Hypotheses

| ID | Hypothesis | Risk | Validation |
|----|-----------|------|------------|
| H3.1 | Signal-grounded content is measurably better than generic | **Critical — this is the product thesis** | Blind A/B, expert rates quality |
| H3.2 | Structured signals are better context than raw transcript chunks | Medium | Same brief, retrieve signals vs. chunks, compare content |
| H3.3 | Retrieval quality is the bottleneck, not generation quality | High — determines investment | Fix retrieval vs. fix generation, measure which moves needle |

### Experiments

**Exp 3.1 — Signal vs. transcript retrieval (Week 4):** 10 content briefs, retrieve signals vs. raw chunks, generate content, blind evaluation. Gate: if signal-grounded isn't significantly better (p < 0.05), re-examine extraction schema.

**Exp 3.2 — Architecture comparison (Week 5):** Three approaches, 30 queries, human-judged relevance. Measure P@5, recall@10, latency, cost. Pick approach with P@5 ≥ 0.7.

**Exp 3.3 — Quality sensitivity (Week 5):** Perfect retrieval → progressively degrade. Find threshold where content quality drops.

### Evaluation

**Offline:** P@5 ≥ 0.7. Content grounding rate ≥ 90% (claims traceable to retrieved signals). Content quality rating with vs. without.

**Online:** Reply rate and time-on-page for intelligence-grounded vs. generic content. User thumbs up/down on retrieved signals.

---

## P4: Outcome Attribution

### P4a: Proxy Metrics & Trajectory Judge (Buildable Now)

**Goal:** Validate leading indicators as outcome proxies. Build LLM-based trajectory judge for fast iteration.

**Exp 4a.1 — Leading indicator validation (Month 2):** Logistic regression from engagement metrics (reply rate, meetings, stage progression) → deal outcomes for 100+ accounts. Target AUC > 0.65.

**Exp 4a.2 — Trajectory judge calibration (Month 2-3):** LLM scores 50 historical deals on trajectory alignment. Measure Spearman correlation with actual outcomes. Gate: if < 0.3, fall back to leading indicators only.

### P4b: Causal Attribution (Long-Term Research)

Confounders everywhere, long feedback loops, small samples per treatment. Approaches in order of feasibility: natural experiments (Amdahl's recommendation ≠ what rep sent → compare outcomes), propensity score matching, randomized A/B (requires customer buy-in). Timeline: 6-12 months after P1-P3 stable.

---

## Critical Assumptions (Kill List)

| Priority | Assumption | If Wrong | Deadline |
|----------|-----------|----------|----------|
| **KILL** | Extraction quality ≥ 80% P/R on surface + behavioral | Foundation broken | Week 2 |
| **KILL** | Schema captures signals marketers find useful | Technically correct but useless | Week 3 |
| **KILL** | Signal-grounded content is measurably better than generic | **Product thesis is wrong** | Week 5 |
| **PIVOT** | Latent signals detectable with > 50% expert agreement | Lose psychographic layer, ship L1+L2 | Week 6 |
| **PIVOT** | Patterns generalize across ≥ 2 industries | Industry-agnostic claim fails, go vertical-first | Month 3 |
| **DEFER** | Leading indicators predict outcomes (AUC > 0.65) | Can't close feedback loop quickly | Month 2 |

KILL = stop and rethink. PIVOT = degrade gracefully. DEFER = doesn't block current work.

---

## Execution Timeline

| Week | Focus | Decision Gate |
|------|-------|---------------|
| 1-2 | P1 extraction + golden set | Surface P/R ≥ 85%? |
| 2-3 | P1 latent signals + schema validation | Marketers find signals useful? |
| 4-5 | P3 retrieval layer | Signal-grounded content better? **Validates product thesis.** |
| 5-6 | End-to-end demo | Transcript → extract → retrieve → content brief working? |
| 7-9 | P2 pattern mining | Aggregated patterns reliable? |
| 8-10 | P4a proxy metrics | Leading indicators predict outcomes? |

---

## Open Research Questions

1. **How do you evaluate psychographic extraction when ground truth is subjective?** Two experts may disagree on a buyer's mental model. We need plausibility scoring and multi-annotator agreement distributions, not binary P/R.

2. **What's the minimum data for meaningful pattern mining?** This determines time-to-value for new customers and is the single most important product-science question.

3. **Does audio add enough signal to justify engineering complexity?** Text-tone divergence is theoretically valuable. Marginal gain over text-only needs a controlled experiment.

4. **How do you handle schema evolution?** The taxonomy will change. Backward compatibility and migration matter from day one.

5. **Is there a "content uncanny valley"?** Content too precisely targeted to someone's psychology might feel manipulative. Where's the ethical line?

6. **Can the trajectory judge learn faster than real outcomes?** If LLM-as-judge correlates with deal outcomes, iterate in hours instead of months. This determines optimization speed.