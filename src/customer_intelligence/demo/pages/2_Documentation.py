"""Page 2: Auto-discovered documentation from docs/ directory."""

from __future__ import annotations

import re

import streamlit as st

from customer_intelligence.demo.data_loader import load_docs


def _extract_description(content: str, max_len: int = 150) -> str:
    """Extract first meaningful line from markdown content as a short description."""
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Skip markdown table headers / separators
        if stripped.startswith("|") or stripped.startswith("---"):
            continue
        if len(stripped) > max_len:
            return stripped[:max_len].rsplit(" ", 1)[0] + "..."
        return stripped
    return ""


def _rewrite_md_links(content: str, available_titles: dict[str, str]) -> str:
    """Replace relative .md links with Streamlit page links using query params.

    ``available_titles`` maps lowercased stem → display title so that
    ``[Setup](setup.md)`` becomes a clickable link to ``?doc=Setup``.
    """

    def _replace(m: re.Match[str]) -> str:
        text = m.group(1)
        href = m.group(2)
        if href.endswith(".md"):
            stem = href.removesuffix(".md").replace("-", " ").replace("_", " ").lower()
            if stem in available_titles:
                title = available_titles[stem]
                return f"[{text}](?doc={title})"
        return m.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace, content)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Documentation")
st.caption("Technical documentation auto-discovered from the `docs/` directory.")

docs = load_docs()

if not docs:
    st.warning("No documentation files found in `docs/` directory.")
else:
    titles = list(docs.keys())

    # Build a lookup from lowercased stem → display title for link rewriting
    stem_to_title: dict[str, str] = {t.lower(): t for t in titles}

    # Check if a specific doc was requested via query param
    selected_doc = st.query_params.get("doc")

    if selected_doc and selected_doc in titles:
        # ----- Doc reader view -----
        if st.button("← Back to all documents"):
            st.query_params.clear()
            st.rerun()

        st.subheader(selected_doc)
        st.divider()
        st.markdown(_rewrite_md_links(docs[selected_doc], stem_to_title))
    else:
        # ----- Card grid list view -----
        st.divider()

        # Render cards in a 2-column grid
        for i in range(0, len(titles), 2):
            cols = st.columns(2)
            for col_idx, col in enumerate(cols):
                doc_idx = i + col_idx
                if doc_idx >= len(titles):
                    break
                title = titles[doc_idx]
                description = _extract_description(docs[title])
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{title}**")
                        if description:
                            st.caption(description)
                        if st.button("Read →", key=f"doc_{doc_idx}"):
                            st.query_params["doc"] = title
                            st.rerun()
