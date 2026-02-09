"""Customer Intelligence Demo — Streamlit multi-page app entry point.

Usage:
    streamlit run src/customer_intelligence/demo/app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Customer Intelligence",
    page_icon="\U0001f9e0",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES_DIR = Path(__file__).parent / "pages"

pg = st.navigation(
    [
        st.Page("home.py", title="Home", icon="\U0001f3e0", default=True),
        st.Page(str(PAGES_DIR / "1_Pipeline_Demo.py"), title="Pipeline Demo", icon="\U0001f9e0"),
        st.Page(str(PAGES_DIR / "2_Documentation.py"), title="Documentation", icon="\U0001f4da"),
    ]
)
pg.run()
