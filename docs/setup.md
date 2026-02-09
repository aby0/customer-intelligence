# Developer Setup

## Prerequisites

- Python >= 3.11
- An [Anthropic API key](https://console.anthropic.com/) for LLM operations

## Installation

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with dev dependencies (pytest, pytest-asyncio).

## Environment

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Both the synthetic generator and signal extractor load this automatically via `python-dotenv`.

## Project Structure

```
src/customer_intelligence/
  schemas/            Pydantic models for inputs and outputs
    transcript.py       Transcript, Utterance, AccountProfile, ParalinguisticAnnotation
    surface.py          Layer 1: aspect sentiment, topics, entities, key phrases
    behavioral.py       Layer 2: objection triples, buying intent, competitive mentions
    psychographic.py    Layer 3: mental models, personas, language fingerprint
    multimodal.py       Text-audio divergence signals
    extraction.py       ExtractionResult (top-level output)
  extraction/         Signal extraction pipeline (Module 1)
    extractor.py        Orchestrator: transcript in, ExtractionResult out
    prompts.py          LLM prompt templates (one per layer)
  synthetic/          Synthetic data generation
    generator.py        LLM-powered transcript + ground truth generation
    profiles.py         Account profiles defining the test corpus
tests/
  test_schemas.py     Schema validation and roundtrip tests
  test_synthetic.py   Corpus coverage validation
  test_extraction.py  Integration tests (extraction vs ground truth)
data/
  transcripts/        Generated synthetic transcripts (JSON)
  ground_truth/       Ground truth extraction annotations (JSON)
spec/                 Architecture and feature specifications
```

## Quick Reference

| Command | What it does | Needs LLM? |
|---------|-------------|------------|
| `python -m customer_intelligence.synthetic.generator` | Generate synthetic corpus | Yes |
| `python -m customer_intelligence.extraction.extractor <file>` | Extract signals from a transcript | Yes |
| `pytest tests/test_schemas.py` | Validate schemas | No |
| `pytest tests/test_synthetic.py` | Validate corpus coverage | No |
| `pytest tests/test_extraction.py -m integration` | Test extraction accuracy vs ground truth | Yes |

See [workflow.md](workflow.md) for detailed step-by-step usage.
