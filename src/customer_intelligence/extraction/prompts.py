"""Prompt templates for each extraction layer.

Each prompt takes a formatted transcript and returns structured JSON
conforming to the corresponding schema.

Prompts are stored as .txt files in the prompts/ directory so they can be
loaded, updated, and tested independently of the Python code.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory.

    Args:
        name: Filename (without .txt extension) of the prompt to load.

    Returns:
        The prompt template string with {transcript} placeholder.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text()


SURFACE_EXTRACTION_PROMPT = load_prompt("surface")
BEHAVIORAL_EXTRACTION_PROMPT = load_prompt("behavioral")
PSYCHOGRAPHIC_EXTRACTION_PROMPT = load_prompt("psychographic")
MULTIMODAL_DIVERGENCE_PROMPT = load_prompt("multimodal_divergence")
SUMMARY_PROMPT = load_prompt("summary")
