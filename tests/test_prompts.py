"""Unit tests for prompt loading and template validity."""

import pytest

from customer_intelligence.extraction.prompts import (
    BEHAVIORAL_EXTRACTION_PROMPT,
    MULTIMODAL_DIVERGENCE_PROMPT,
    PROMPTS_DIR,
    PSYCHOGRAPHIC_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
    SURFACE_EXTRACTION_PROMPT,
    load_prompt,
)


PROMPT_NAMES = ["surface", "behavioral", "psychographic", "multimodal_divergence", "summary"]


class TestLoadPrompt:
    """Test the load_prompt function."""

    @pytest.mark.parametrize("name", PROMPT_NAMES)
    def test_loads_existing_prompt(self, name: str):
        prompt = load_prompt(name)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_raises_on_missing_prompt(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt")

    @pytest.mark.parametrize("name", PROMPT_NAMES)
    def test_prompt_has_transcript_placeholder(self, name: str):
        prompt = load_prompt(name)
        assert "{transcript}" in prompt, f"{name} prompt missing {{transcript}} placeholder"

    @pytest.mark.parametrize("name", PROMPT_NAMES)
    def test_prompt_can_be_formatted(self, name: str):
        prompt = load_prompt(name)
        result = prompt.format(transcript="Hello, world.")
        assert "Hello, world." in result
        assert "{transcript}" not in result


class TestModuleLevelPrompts:
    """Test that module-level prompt constants are loaded correctly."""

    def test_surface_prompt_loaded(self):
        assert len(SURFACE_EXTRACTION_PROMPT) > 0
        assert "{transcript}" in SURFACE_EXTRACTION_PROMPT

    def test_behavioral_prompt_loaded(self):
        assert len(BEHAVIORAL_EXTRACTION_PROMPT) > 0
        assert "{transcript}" in BEHAVIORAL_EXTRACTION_PROMPT

    def test_psychographic_prompt_loaded(self):
        assert len(PSYCHOGRAPHIC_EXTRACTION_PROMPT) > 0
        assert "{transcript}" in PSYCHOGRAPHIC_EXTRACTION_PROMPT

    def test_multimodal_prompt_loaded(self):
        assert len(MULTIMODAL_DIVERGENCE_PROMPT) > 0
        assert "{transcript}" in MULTIMODAL_DIVERGENCE_PROMPT

    def test_summary_prompt_loaded(self):
        assert len(SUMMARY_PROMPT) > 0
        assert "{transcript}" in SUMMARY_PROMPT


class TestPromptFiles:
    """Test that all expected prompt files exist on disk."""

    @pytest.mark.parametrize("name", PROMPT_NAMES)
    def test_prompt_file_exists(self, name: str):
        path = PROMPTS_DIR / f"{name}.txt"
        assert path.exists(), f"Missing prompt file: {path}"

    def test_no_unexpected_prompt_files(self):
        expected = {f"{name}.txt" for name in PROMPT_NAMES}
        actual = {f.name for f in PROMPTS_DIR.glob("*.txt")}
        unexpected = actual - expected
        assert not unexpected, f"Unexpected prompt files: {unexpected}"
