# Feature: Pipeline Architecture

**Date**: 2026-02-07
**Status**: WIP
**Last updated**: 2026-02-07

## User Value

Marketers and content strategists need more than keyword searches over raw transcripts — they need structured, queryable customer intelligence that reveals *how customers think and decide*. The pipeline architecture defines a three-module system that transforms sales call recordings into actionable signals, discovers cross-account patterns, and makes those insights retrievable for content generation.

## How It Works

The pipeline processes sales call transcripts through three sequential modules, each building on the output of the previous one:

**Module 1 — Signal Extraction** takes a single sales call transcript (with optional paralinguistic annotations) and produces structured JSON containing signals at three layers of depth: surface signals (entities, topics, aspect-level sentiment), behavioral signals (objections, buying intent, competitive mentions, engagement trajectory), and psychographic signals (buyer mental model, language fingerprint, persona indicators). When multimodal annotations are present, the system detects text-audio divergence — cases where what the customer *says* contradicts *how they say it*.

**Module 2 — Pattern Mining** (deferred) aggregates extracted signals across many calls and accounts to discover patterns: which objection-resolution sequences correlate with deal progression, what behavioral persona clusters exist in the customer base, and how engagement trajectories predict outcomes. This is where individual call intelligence becomes a strategic data asset.

**Module 3 — Content Retrieval** (deferred) accepts a content brief (e.g., "Write a case study targeting analytical CFOs with pricing concerns") and retrieves the most relevant customer signals, direct quotes, and cross-account patterns to ground content generation in real customer voice.

The architecture is designed to be **industry-agnostic**: the pipeline structure (stages, signal types, evaluation dimensions) is universal, while the specific vocabulary — objections, proof points, personas — is learned from each customer's data.

## Key Interactions

- **When a transcript is processed**: Module 1 extracts all three signal layers and produces a structured JSON document per call. Each extraction includes confidence scores and provenance (which utterances support each signal).
- **When signals span multiple calls for one account**: Module 2 merges signals temporally, tracking how engagement, sentiment, and objection status evolve across touchpoints.
- **When a content brief is submitted**: Module 3 retrieves signals by semantic similarity, filtered by persona, deal stage, and signal type. Results include direct quotes with context.
- **When text-audio divergence is detected**: The system flags the utterance as a "latent signal" and adjusts composite sentiment confidence. Hidden objections (positive text + negative audio cues) surface explicitly rather than being masked.
- **Edge case — insufficient data**: For accounts with only one call, Module 2 falls back to cohort-level patterns (similar accounts) rather than account-specific trajectories.
- **Edge case — new industry vertical**: The pipeline uses the same extraction schema but discovers industry-specific patterns through clustering rather than hard-coding them.

## Acceptance Criteria

- [ ] Pipeline defines clear input/output schemas for each module boundary (Module 1 output is Module 2 input, etc.)
- [ ] Module 1 extracts signals at all three layers (surface, behavioral, psychographic) from a single transcript
- [ ] Signal extraction produces structured JSON conforming to a defined schema with confidence scores
- [ ] Architecture supports processing multiple transcripts per account with temporal ordering
- [ ] Module boundaries are cleanly separated — each module can be developed, tested, and run independently
- [ ] Extraction schemas are industry-agnostic (no hard-coded domain vocabulary in the schema structure)
- [ ] System handles transcripts with and without paralinguistic annotations (graceful degradation)

## Related Features

- [Signal Extraction (Module 1)](2026-02-07-signal-extraction.md) — detailed spec for the first module
- [Synthetic Data Generation](2026-02-07-synthetic-data-generation.md) — provides test data for the pipeline

## Design Decisions

- **Why three layers?** Surface signals are table stakes (well-solved NLP). Behavioral signals differentiate (require understanding conversation dynamics). Psychographic signals are the hard problem (customer psychology at scale). This layering reflects increasing extraction difficulty and increasing business value.
- **Why modules, not a monolith?** Each module has different data requirements (single call vs. cross-account vs. query-time), different iteration cycles, and different evaluation methods. Loose coupling enables independent development and testing.
- **Why LLM-based extraction over custom models?** For a POC, LLMs with structured output schemas provide the fastest path to multi-layer extraction without training data. The schema-first approach means switching to fine-tuned models later requires changing the extraction engine, not the pipeline architecture.
- **Why industry-agnostic by design?** Amdahl's platform serves multiple verticals. Hard-coding domain knowledge limits scalability. The architecture learns domain vocabulary from data while keeping the structural framework (stages, personas, objection types) universal.

## Notes

- The RL-inspired evaluation framework (deal trajectory scoring, process reward models) applies across the full pipeline but is out of POC scope — we focus on extraction quality evaluation first
- Module 2 and Module 3 specs will be drafted after Module 1 is built and validated
- The pipeline is batch/post-hoc for the POC; real-time processing is a future consideration
