# RL for Content Strategy Optimization

*Why reinforcement learning is the right framework for GTM content — and a practical research path from heuristics to learned policies.*

---

## The Principle

Most content tools are **open-loop**: generate → publish → hope it works. Performance is measured by vanity metrics (clicks, impressions), not business outcomes (pipeline, revenue).

This is a **sequential decision problem**. A deal isn't won by one email — it's won by a sequence of content touches, each responding to how the customer's state has evolved. An ROI case study is the right move for an analytical evaluator with a pricing objection. It's wrong for an executive champion in discovery. Same content, different context, different outcome.

RL models this explicitly: an agent (content system) observes a state (customer intelligence), takes an action (content choice), receives a reward (deal progression), and learns a policy (optimal content strategy).

| RL Concept | Amdahl Application |
|-----------|-------------------|
| **State** | Customer profile: persona, stage, objections, engagement trajectory, mental model |
| **Action** | Content choice: template, case study, ROI calculator — plus channel and timing |
| **Reward** | Deal progression: stage advance (+10), meeting booked (+3), closed-won (+100), silence (-3) |
| **Episode** | Full customer journey, first touch to close |
| **Policy** | Optimal content sequence for a given customer state |

### Why This Is Hard

**Sparse, delayed rewards.** Months between content and outcome. Most actions get no immediate feedback.

**Partial observability.** We see what customers say, not what they think. Psychographic extraction is our best approximation, but the state is always incomplete.

**Non-stationarity.** What worked last quarter may not work this quarter. The policy must adapt.

---

## Research Direction: Three Stages

Each stage is independently useful and builds on the last.

### Stage 1: Contextual Bandits (~200 examples)

The simplest useful formulation. No sequential dependence — just "given this customer state, which content action performs best?"

State features from P1 extraction + logged content action + outcome (progression/no progression). Fit a contextual bandit (LinUCB or Thompson Sampling). The bandit learns: "For analytical evaluators with pricing objections, ROI calculators progress deals 2.3x more than case studies." Thompson Sampling naturally balances exploration (trying new strategies) with exploitation (using known-good ones).

**Data:** ~200 content-action-outcome triples. At 20 deals/month, ~3 months of logging.

### Stage 2: Sequential Recommendation (~500 timelines)

Content A only works because Content B preceded it. The bandit ignores this.

**Approach (simplest first):**

**Sequence modeling:** Treat winning deal timelines as training sequences. Predict next-best content action given the sequence so far — conceptually similar to Decision Transformer, framing RL as sequence prediction. The model learns: "After an ROI argument partially resolves a pricing objection, the next-best action is a peer reference, not more data."

**Fitted Q-iteration:** Learn Q(state, action) — expected cumulative reward for taking an action in a given state. Offline RL from logged data. Advantage: Q-values explain *why* one action is better.

**Full policy learning (future):** PPO or similar, optimizing against a learned reward model. Requires online experimentation with customer buy-in.

**Data:** ~500 account timelines. Accelerated by cross-customer learning.

### Stage 3: Process Reward Model (The Differentiator)

Borrowed from math reasoning research (Let's Verify Step by Step). The key insight: **score at each deal stage, not just win/loss.**

```
Outcome Reward Model: deal closed → +100 (one signal, after months)

Process Reward Model:
  Discovery → Evaluation:  content moved deal forward?    +10
  Evaluation → Negotiation: objection addressed?           +15
  Negotiation → Close:      proposal requested?            +20
  Close → Won:              deal signed?                   +50
  (4-6x more training signal per deal)
```

A deal that progresses from Discovery to Evaluation before stalling still teaches you what worked in that first transition. PRMs make learning tractable with limited data.

**Implementation:** The PRM can be an LLM-based trajectory judge that evaluates content recommendations against winning deal patterns. Score on stage appropriateness, persona alignment, objection addressing, trajectory alignment with winning deals. If judge scores correlate with actual stage transitions (Spearman > 0.4), you have a fast-iteration proxy — iterate in hours instead of months.

---

## Credit Assignment

The hardest RL problem: if a deal closes after 15 content touches, which ones mattered?

**Temporal difference (buildable now):** Compare expected deal value before vs. after each content action. ROI case study moved close probability from 30% → 55%? That action gets credit for the 25-point change.

**Counterfactual analysis (needs data):** Match accounts by profile, compare those that received specific content vs. those that didn't. Propensity score matching for observable confounders.

**Trajectory comparison (pattern-based):** Align winning vs. losing deal timelines. What content actions appear in wins but not losses? Simple, interpretable, correlation not causation.

---

## Connection to RLHF

The parallel is direct: base model = content generation LLM, SFT = fine-tune on winning deals, reward model = deal trajectory judge, PPO = optimize content strategy, KL penalty = brand voice constraint, PRM = per-stage scoring.

**The DPO shortcut:** Skip the reward model entirely. Directly optimize from paired examples: "For this customer state, Content A led to progression, Content B didn't." No explicit reward model needed. This may be the fastest path to a working system.

---

## Experiments

| ID | Experiment | Data Needed | Decision Gate |
|----|-----------|-------------|---------------|
| R1 | **Reward signal validation.** Logistic regression: leading indicators → deal outcome. | 100 accounts | AUC > 0.65? If no, RL has no foundation. |
| R2 | **Bandit simulation.** Offline evaluation: does state-matched content outperform random? | 200 action-outcome pairs | Progression rate improvement? |
| R3 | **Sequence effect detection.** Same content, different order — does order matter? | 500 timelines | If no, stay with bandits. Don't build sequential RL. |
| R4 | **PRM calibration.** LLM judge scores 50 deals. Correlate with actual outcomes. | 50 historical deals | Spearman > 0.4? If no, fall back to leading indicators. |
| R5 | **DPO on content pairs.** Train policy from win/loss pairs. Evaluate via trajectory judge. | 500 content pairs | Judge prefers optimized policy's recommendations? |

---

## What's Buildable When

| Timeline | Build | Data |
|----------|-------|------|
| **Now (POC)** | State representation from P1 extraction — the features an RL agent would use | 5 transcripts |
| **Month 2** | Reward signal validation (R1) | 100 accounts |
| **Month 3** | Contextual bandit, offline (R2) | 200 pairs |
| **Month 4** | PRM / trajectory judge (R4) | 50 deals |
| **Month 6** | DPO optimization (R5) | 500 pairs |
| **Month 12+** | Full sequential policy with online exploration | 1000+ timelines |

**The critical insight: you don't need RL to start. You need a good state representation.** P1 (signal extraction) builds the state. The bandit, the PRM, and the full policy are all downstream consumers. Get the state right first.

---

## Failure Modes

| Failure | Fallback |
|---------|----------|
| Leading indicators don't predict outcomes | Expert heuristics for content strategy. System still provides extraction + retrieval value. |
| Bandit shows no improvement over random | State representation is poor (invest in P1) or content choice genuinely doesn't matter (revisit product thesis). |
| Sequence effects don't exist | Stay with bandits. Simpler, sufficient. Don't build sequential RL. |
| PRM doesn't correlate with outcomes | Use as sanity check only. Rely on actual outcomes for optimization. |
| Not enough data for any RL approach | Log everything. Aggregate across customers — patterns from Customer A's deals inform recommendations for Customer B. This is where the intelligence graph becomes a data flywheel. |