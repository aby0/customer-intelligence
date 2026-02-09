"""Traditional NLP baselines for cross-validation of LLM extraction.

All baselines degrade gracefully when optional libraries are not installed.
Install with: pip install customer-intelligence[eval]
"""

from __future__ import annotations


class BaselineUnavailableError(ImportError):
    """Raised when an optional NLP library is not installed."""


def spacy_ner_baseline(text: str) -> set[str]:
    """Extract named entities using spaCy as a reference baseline.

    Returns a set of entity text strings (lowercased).
    Requires: pip install spacy && python -m spacy download en_core_web_sm
    """
    try:
        import spacy
    except ImportError:
        raise BaselineUnavailableError(
            "spaCy not installed. Run: pip install spacy && "
            "python -m spacy download en_core_web_sm"
        )

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise BaselineUnavailableError(
            "spaCy model not found. Run: python -m spacy download en_core_web_sm"
        )

    doc = nlp(text)
    return {ent.text.lower() for ent in doc.ents}


def keyphrase_baseline(text: str, top_n: int = 20) -> set[str]:
    """Extract key phrases using YAKE as a reference baseline.

    Returns a set of keyphrase strings (lowercased).
    Requires: pip install yake
    """
    try:
        import yake
    except ImportError:
        raise BaselineUnavailableError("YAKE not installed. Run: pip install yake")

    extractor = yake.KeywordExtractor(
        lan="en", n=3, dedupLim=0.9, top=top_n, features=None,
    )
    keywords = extractor.extract_keywords(text)
    return {kw.lower() for kw, _score in keywords}


def sentiment_baseline(text: str) -> str:
    """Classify sentiment polarity using TextBlob as a reference baseline.

    Returns "positive", "negative", or "neutral".
    Requires: pip install textblob
    """
    try:
        from textblob import TextBlob
    except ImportError:
        raise BaselineUnavailableError(
            "TextBlob not installed. Run: pip install textblob"
        )

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"


def compute_entity_baseline_agreement(
    extracted_entities: set[str], transcript_text: str,
) -> float | None:
    """Fraction of spaCy-detected entities found in extraction output."""
    try:
        spacy_entities = spacy_ner_baseline(transcript_text)
    except BaselineUnavailableError:
        return None

    if not spacy_entities:
        return None

    found = 0
    for se in spacy_entities:
        for ee in extracted_entities:
            if se in ee or ee in se:
                found += 1
                break

    return found / len(spacy_entities)


def compute_keyphrase_baseline_agreement(
    extracted_phrases: set[str], transcript_text: str,
) -> float | None:
    """Fraction of YAKE key phrases found in extraction output."""
    try:
        yake_phrases = keyphrase_baseline(transcript_text)
    except BaselineUnavailableError:
        return None

    if not yake_phrases:
        return None

    found = 0
    for yp in yake_phrases:
        yp_tokens = set(yp.split())
        for ep in extracted_phrases:
            ep_tokens = set(ep.lower().split())
            if yp_tokens & ep_tokens:
                found += 1
                break

    return found / len(yake_phrases)


def compute_sentiment_baseline_agreement(
    extracted_polarities: list[tuple[str, str]],
    utterance_texts: dict[int, str],
) -> float | None:
    """Agreement between extracted aspect sentiments and TextBlob on source utterances.

    extracted_polarities: list of (source_text, extracted_polarity) pairs.
    """
    try:
        from textblob import TextBlob  # noqa: F401
    except ImportError:
        return None

    if not extracted_polarities:
        return None

    matches = 0
    for source_text, ext_polarity in extracted_polarities:
        baseline_polarity = sentiment_baseline(source_text)
        # Map "mixed" to neutral for comparison
        ext_mapped = "neutral" if ext_polarity == "mixed" else ext_polarity
        if ext_mapped == baseline_polarity:
            matches += 1

    return matches / len(extracted_polarities)
