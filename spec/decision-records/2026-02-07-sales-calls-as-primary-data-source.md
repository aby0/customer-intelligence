# Decision: Sales Calls as Primary Data Source for POC

**Date**: 2026-02-07
**Status**: Active
**Domain**: Data Architecture

## The Question

Amdahl's full platform ingests data from multiple sources (Gong sales calls, Salesforce CRM, support tickets). Which data source should the POC focus on?

## Decision

Focus the POC exclusively on **sales call transcripts** (e.g., from Gong, Fathom). CRM data and support tickets are intentionally out of scope.

## Rationale

Sales calls are the richest single source of customer intelligence. They contain the unfiltered voice of the customer — objections, enthusiasm, hesitation, and decision-making patterns that structured CRM fields cannot capture.

- **CRM data is structured and shallow**: deal stage, revenue, dates. Useful for labeling outcomes, but not for understanding *how* customers think.
- **Support tickets reveal post-sale sentiment**: valuable, but don't inform the pre-sale content strategy that drives revenue.
- **Sales calls reveal decision-making psychology**: how customers evaluate, what objections they raise, how they respond to different arguments, what language they use. This is the raw material for intelligent content generation.

By proving the pipeline on the highest-signal source first, we validate the extraction architecture before adding lower-signal inputs. The architecture is designed to accommodate additional data sources later — the extraction schemas are extensible, and the pattern mining layer can fuse signals from multiple sources.

## User Impact

- Content generated from sales call intelligence will reflect actual customer voice, objections, and decision patterns
- Initial content recommendations will be grounded in how customers *talk about their problems*, not CRM metadata
- Missing CRM context (deal stage, revenue) means some pattern mining will use synthetic outcome labels in the POC

## Implementation Notes

- Synthetic sales call transcripts substitute for real Gong recordings in the POC
- Transcripts include paralinguistic annotations (pauses, hesitation markers, energy levels) to simulate multimodal signals
- Architecture should define clear interfaces for future data source integration (CRM enrichment, support ticket sentiment)

## Constraints

- No access to real Gong API or customer transcripts for the POC
- POC must demonstrate value from a single data source to justify multi-source expansion
- Interview timeline limits scope to what's buildable and demonstrable quickly

## Alternatives Considered

- **All sources simultaneously**: Pros — richer signals, full Amdahl pipeline. Cons — too broad for POC, integration complexity dominates over intelligence extraction quality. Rejected because it dilutes focus on the hard problem (deep signal extraction).
- **CRM data first**: Pros — structured, easy to ingest and model. Cons — shallow signals, doesn't demonstrate NLP capability, doesn't differentiate from existing tools. Rejected because it doesn't showcase the core technical challenge.
- **Support tickets first**: Pros — text-based, familiar NLP task. Cons — post-sale only, limited buying psychology signal. Rejected because it doesn't serve the revenue-focused content generation use case.

## Related Decisions

- Pipeline Architecture (feature spec) — defines the modular structure that enables future data source additions

## Timeline

- **2026-02-07**: Decision made during initial spec drafting
