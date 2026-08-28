"""
Home page & app entry point.

Run from the project root with:
    streamlit run app/app.py
"""

import sys
from pathlib import Path

# Make the project root importable (so `data.crops`, `models.predictor`,
# `chatbot.qwen_assistant`, `app.components.*` all resolve regardless of
# where Streamlit is launched from).
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.styles.theme import inject_theme
from app.components.nav import render_sidebar
from app.components.state import init_state
from app.components.ui import hero, divider
from data.crops import SUPPORTED_CROPS

st.set_page_config(
    page_title="Plant Health AI — Disease & Severity Detection",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
inject_theme()
render_sidebar(active="home")

# ---------------------------------------------------------------- HERO ----
left, right = st.columns([1.15, 0.85], gap="large")

with left:
    hero(
        title_html='Know what\'s wrong with your crop<br><span class="hero-accent">before it spreads.</span>',
        subtitle=(
            "Plant Health AI reads a single leaf photo and returns a disease "
            "diagnosis, a confidence score, and a severity read-out — then "
            "an assistant walks you through what to do next. Built for "
            "quick use in the field, on any phone."
        ),
    )
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        if st.button("🔬  Start Diagnosis", type="primary", use_container_width=True):
            st.switch_page("pages/1_🔬_Diagnosis.py")
    with c2:
        if st.button("Learn how it works", type="secondary", use_container_width=True):
            st.switch_page("pages/4_ℹ️_About.py")

    st.markdown(
        """
        <div style="display:flex; gap:1.6rem; margin-top:2rem; flex-wrap:wrap;">
            <div><span class="stat-value" style="font-size:1.3rem;">12</span>
                 <div class="stat-label">Supported crops</div></div>
            <div><span class="stat-value" style="font-size:1.3rem;">3</span>
                 <div class="stat-label">Severity tiers</div></div>
            <div><span class="stat-value" style="font-size:1.3rem;">&lt;10s</span>
                 <div class="stat-label">Typical analysis time</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="card" style="margin-top:2.4rem;">
            <div class="eyebrow">Sample read-out</div>
            <h3 style="margin-top:0.3rem;">Tomato · Early Blight</h3>
            <div style="display:flex; gap:1.6rem; margin-top:0.8rem;">
                <div>
                    <div class="stat-label">Confidence</div>
                    <div class="stat-value">93%</div>
                </div>
                <div>
                    <div class="stat-label">Severity</div>
                    <div class="stat-value" style="font-size:1.65rem;">
                        <span class="badge badge-moderate">▲ Moderate</span>
                    </div>
                </div>
            </div>
            <div class="divider-line" style="margin:1.2rem 0;"></div>
            <div class="eyebrow">Assistant</div>
            <p style="margin-top:0.4rem; color:var(--muted); font-size:0.92rem;">
                "Remove affected leaves, improve airflow, and monitor the plant
                over the next few days — full management guidance is available
                once your diagnosis is ready."
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

divider()

# ------------------------------------------------------------ HOW IT WORKS
st.markdown('<div class="eyebrow">How it works</div>', unsafe_allow_html=True)
st.markdown("## From leaf photo to guidance in four steps")

steps = [
    ("01", "Select your crop", "Choose from the supported crop list so the model knows what it's looking at."),
    ("02", "Upload or capture a leaf", "Take a clear photo of the affected leaf, or upload one from your gallery."),
    ("03", "Get disease & severity", "The model returns a diagnosis, a confidence score, and a Mild / Moderate / Severe rating."),
    ("04", "Ask the assistant", "Get plain-language management guidance grounded in your specific result."),
]

cols = st.columns(4, gap="medium")
for col, (num, title, desc) in zip(cols, steps):
    with col:
        st.markdown(
            f"""
            <div class="card tight" style="height:100%;">
                <div class="step-num">{num}</div>
                <div style="font-weight:700; margin-top:0.4rem; color:var(--forest-900);">{title}</div>
                <div style="font-size:0.85rem; color:var(--muted); margin-top:0.3rem;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

divider()

# --------------------------------------------------------- SUPPORTED CROPS
st.markdown('<div class="eyebrow">Coverage</div>', unsafe_allow_html=True)
st.markdown("## Supported crops")
st.markdown(
    '<p style="color:var(--muted); margin-top:-0.6rem;">'
    "More crops will be added as the underlying model is retrained on additional data."
    "</p>",
    unsafe_allow_html=True,
)

crop_cols = st.columns(4, gap="small")
for i, crop in enumerate(SUPPORTED_CROPS):
    with crop_cols[i % 4]:
        st.markdown(
            f"""
            <div class="crop-card">
                <div class="crop-emoji">{crop['emoji']}</div>
                <div class="crop-name">{crop['label']}</div>
                <div class="crop-blurb">{crop['blurb']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")
st.write("")
if st.button("🔬  Start Diagnosis Now", type="primary"):
    st.switch_page("pages/1_🔬_Diagnosis.py")

st.markdown(
    '<div class="footer-note">Plant Health AI · Hackathon MVP · '
    "Predictions are decision support, not a substitute for expert diagnosis.</div>",
    unsafe_allow_html=True,
)
