# Customer Intelligence Pipeline

An AI-powered pipeline that extracts deep, actionable signals from **sales call transcripts** and uses them to drive revenue-focused content generation. Built for [Amdahl AI](https://amdahl.ai) — a content orchestration platform that transforms unstructured customer data into intelligent, persona-aware marketing content.

## The Core Problem

Surface-level NLP (sentiment polarity, keyword extraction) tells you *what* customers said. The real value is understanding *how customers think, what they'll do next, and how to talk to them*. This pipeline bridges that gap by extracting signals at three layers of depth — from surface entities to behavioral patterns to psychographic traits — and making them retrievable for content generation.

## User Workflows

### 1. Signal Extraction (Module 1)
A sales call transcript (with optional paralinguistic annotations) goes in. Structured intelligence comes out — aspect-level sentiment, objection patterns, buying intent markers, persona indicators, and multimodal divergence flags. This is the foundation everything else builds on.

### 2. Pattern Mining (Module 2) — *deferred*
Signals from many calls are aggregated to discover cross-account patterns: which objection-resolution combos actually work, what behavioral personas exist in the customer base, and how engagement trajectories predict deal outcomes.

### 3. Content Retrieval (Module 3) — *deferred*
A content brief ("Write a case study targeting CFOs concerned about implementation cost") retrieves the most relevant customer signals, quotes, and patterns to ground the generated content in real customer voice.

## Constraints & Non-Goals

**Does not do:**
- CRM data ingestion (Salesforce) — out of POC scope
- Support ticket analysis — out of POC scope
- Real-time call coaching — batch/post-hoc analysis only for POC
- Content generation — retrieval only; generation is Amdahl's existing capability
- Full RL policy learning — we extract RL-relevant features (state representation), not train policies

**Operating constraints:**
- POC uses synthetic sales call data (no real Gong recordings available)
- Multimodal signals (audio prosody, video) are simulated via transcript annotations
- Architecture must be industry-agnostic: universal structure, domain-specific parameters learned from data
- LLM-based extraction with structured output schemas (no custom model training for POC)

## Features

See [features/README.md](features/README.md)

## Decisions

See [decision-records/README.md](decision-records/README.md)

## Recent Changes

- **2026-02-07**: Initial specs drafted — Pipeline Architecture, Signal Extraction (Module 1), Synthetic Data Generation
