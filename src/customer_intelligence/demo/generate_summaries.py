"""One-time script to pre-generate TranscriptSummary data for all transcripts.

Usage:
    python -m customer_intelligence.demo.generate_summaries
"""

from __future__ import annotations

import json
from pathlib import Path

from customer_intelligence.extraction.extractor import extract_summary
from customer_intelligence.schemas.transcript import Transcript

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRANSCRIPTS_DIR = PROJECT_ROOT / "data" / "transcripts"
SUMMARIES_DIR = PROJECT_ROOT / "data" / "summaries"


def main() -> None:
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    if not transcript_files:
        print(f"No transcripts found in {TRANSCRIPTS_DIR}")
        return

    for path in transcript_files:
        call_id = path.stem
        out_path = SUMMARIES_DIR / f"{call_id}.json"

        if out_path.exists():
            print(f"  Skipping {call_id} (already exists)")
            continue

        print(f"  Generating summary for {call_id}...")
        transcript = Transcript.model_validate_json(path.read_text())
        summary = extract_summary(transcript)
        out_path.write_text(summary.model_dump_json(indent=2))
        print(f"  Saved {out_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
