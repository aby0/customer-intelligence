# Streamlit App: Product Demo + Technical Documentation

## Context

You want to share the customer intelligence pipeline with stakeholders who don't have time to read code. The app serves two purposes: (1) an interactive product demo showing what the pipeline extracts from sales calls, and (2) documentation pages covering the approach, evaluation methodology, and future roadmap for Modules 2 & 3. All in one Streamlit multi-page app.

**On Modules 2 & 3**: Don't build them. Module 1 with its evaluation framework is already a strong demonstration. A "Future Approach" page in the app documents the thinking for Modules 2 & 3 without weeks of implementation work.

## Data Available

- 10 transcripts in `data/transcripts/`, 8 with extractions (7 ground truth + 1 pipeline output)
- **No pre-generated summaries** — `extract_summary()` exists in `src/customer_intelligence/extraction/extractor.py` but `data/summaries/` doesn't exist yet. We'll add a one-time generation script to pre-compute summaries for all transcripts so the demo runs without API calls.
- Existing docs: `spec/README.md` (architecture overview), `docs/evaluation.md` (eval methodology), `docs/workflow.md` (pipeline workflow), feature specs for all 3 modules

## App Structure (Multi-Page Streamlit)

### Page 1: Pipeline Demo (interactive)
- **Sidebar**: Call selector dropdown, metadata cards (company, stage, outcome, confidence)
- **Tabs**: Summary | Conversation | Surface Signals | Behavioral Signals | Psychographic Profile | Multimodal | Actionable Insights
- **Summary tab** (new, first tab): Executive summary, key moments, action items, prospect priorities, concerns — from pre-generated `TranscriptSummary` data. Gives stakeholders the "what happened" before they dive into signals.
- Loads pre-computed data from `data/` — no API calls needed
- Each tab includes a brief "why this matters" callout for non-technical readers

### Page 2: Documentation (auto-discovered from `docs/`)
- App scans `docs/` directory and renders every `.md` file as a navigable section
- Files sorted alphabetically; the filename (minus `.md`) becomes the section title
- You can add/remove/edit docs without touching app code — just drop `.md` files in `docs/`
- Current docs that will appear: setup, workflow, evaluation
- You can add more (e.g., `docs/approach.md`, `docs/architecture.md`, `docs/future-roadmap.md`) at any time

## New Files

```
docs/plans/streamlit-demo.md     # this plan, saved to docs for reference

src/customer_intelligence/demo/
  __init__.py              # empty
  app.py                   # page config + multi-page navigation (~50 lines)
  generate_summaries.py    # one-time script to pre-generate TranscriptSummary data
  pages/
    1_Pipeline_Demo.py     # interactive call explorer with summary tab (~400 lines)
    2_Documentation.py     # auto-discovers and renders all .md files from docs/ (~60 lines)
  components.py            # shared rendering functions for demo page (~350 lines)
  data_loader.py           # JSON loading + Pydantic validation, cached (~80 lines)
  insights.py              # synthesize actionable insights from extraction data (~100 lines)
```

## Modified Files

- `pyproject.toml` — add `demo = ["streamlit>=1.40.0", "plotly>=5.20.0"]` to `[project.optional-dependencies]`

## Implementation Steps

### Step 0: Save plan to `docs/plans/streamlit-demo.md`

### Step 1: Pre-generate summaries
Create `src/customer_intelligence/demo/generate_summaries.py` — a script that runs `extract_summary()` from `src/customer_intelligence/extraction/extractor.py` for all 10 transcripts and saves results to `data/summaries/{call_id}.json`. One-time API cost so the demo app loads instantly with no API dependency.

### Step 2: `data_loader.py`
- `load_transcripts()`, `load_extractions()`, and `load_summaries()` with `@st.cache_data`
- Ground truth loads first, pipeline extractions override
- `get_display_label(transcript)` for dropdown formatting
- `load_docs()` — scans `docs/` dir, returns dict of `{title: markdown_content}`
- Reuse Pydantic models from `src/customer_intelligence/schemas/`

### Step 3: `components.py`
One `render_*` function per demo tab:
- `render_summary(summary)` — executive summary, key moments (with type badges), action items, prospect priorities, concerns to address. Uses `TranscriptSummary` schema from `src/customer_intelligence/schemas/summary.py`
- `render_conversation(transcript)` — chat bubbles via `st.chat_message`, paralinguistic tags
- `render_surface(surface)` — Plotly horizontal bar for aspect sentiment, topic timeline, entity table, phrase tags
- `render_behavioral(behavioral)` — objection triple cards (3-column: objection→resolution→outcome), intent markers, competitive mentions, engagement trajectory
- `render_psychographic(psychographic)` — mental model card, persona confidence bars (Plotly), language fingerprint columns
- `render_multimodal(multimodal, transcript)` — divergence signals with utterance context, composite sentiment before/after

Key schemas referenced:
- `src/customer_intelligence/schemas/summary.py` — TranscriptSummary, KeyMoment, ActionItem
- `src/customer_intelligence/schemas/surface.py` — AspectSentiment, TopicDetection, NamedEntity, KeyPhrase
- `src/customer_intelligence/schemas/behavioral.py` — ObjectionTriple, BuyingIntentMarker, CompetitiveMention, EngagementTrajectoryPoint
- `src/customer_intelligence/schemas/psychographic.py` — MentalModel, PersonaIndicator, LanguageFingerprint
- `src/customer_intelligence/schemas/multimodal.py` — DivergenceSignal, CompositeSentiment

### Step 4: `insights.py`
Pure Python logic for the "Actionable Insights" tab:
- `generate_key_findings(extraction)` — mental model insight, objection resolution rate, intent marker strength
- `generate_content_recommendations(extraction)` — persona-based content type suggestions
- `generate_risk_flags(extraction)` — unresolved objections, declining engagement, divergence warnings

### Step 5: `pages/1_Pipeline_Demo.py`
Sidebar with call selector + metadata. 7 tabs: Summary | Conversation | Surface | Behavioral | Psychographic | Multimodal | Actionable Insights. Graceful fallback for calls without extraction/summary data.

### Step 6: `pages/2_Documentation.py`
Auto-discovers all `.md` files in `docs/`. Renders each as a selectable section using `st.selectbox` or expandable sections. Filename becomes the title (e.g., `evaluation.md` → "Evaluation"). No hardcoded content — just drop new `.md` files in `docs/` and they appear.

### Step 7: `app.py`
Entry point with `st.set_page_config(layout="wide")` and multi-page navigation setup.

### Step 8: Update `pyproject.toml`
Add demo dependency group.

### Step 9: Run `generate_summaries.py`
Execute the script to populate `data/summaries/`.

## Verification

```bash
# Generate summaries first (one-time, requires ANTHROPIC_API_KEY)
python -m customer_intelligence.demo.generate_summaries

# Install and run
pip install -e ".[demo]"
streamlit run src/customer_intelligence/demo/app.py
```

Then verify:
- **Demo page**: Select TechCorp Call 1 — Summary tab shows executive summary, key moments, action items
- **Demo page**: All 7 tabs render (Summary, Conversation, Surface, Behavioral, Psychographic, Multimodal, Actionable Insights)
- **Demo page**: Select Meridian Healthcare (no extraction) — shows graceful fallback
- **Docs page**: All 3 current docs (setup, workflow, evaluation) render correctly
- **Docs page**: Add a new `.md` file to `docs/`, refresh — it appears automatically
- **Navigation**: Multi-page sidebar works across both pages
