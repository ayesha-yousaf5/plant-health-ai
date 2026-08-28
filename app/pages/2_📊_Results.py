import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.styles.theme import inject_theme
from app.components.nav import render_sidebar
from app.components.state import init_state, reset_diagnosis
from app.components.ui import eyebrow, divider, severity_badge, gauge_card
from data.crops import SUPPORTED_CROPS

st.set_page_config(page_title="Results · Plant Health AI", page_icon="📊", layout="wide")

init_state()
inject_theme()
render_sidebar(active="results")

result = st.session_state.get("diagnosis_result")
image = st.session_state.get("uploaded_image")

if result is None or image is None:
    eyebrow("Step 4")
    st.markdown("## No diagnosis yet")
    st.markdown(
        '<p style="color:var(--muted);">Run a diagnosis first to see results here.</p>',
        unsafe_allow_html=True,
    )
    if st.button("🔬  Go to Diagnosis", type="primary"):
        st.switch_page("pages/1_🔬_Diagnosis.py")
    st.stop()

crop_label = next((c["label"] for c in SUPPORTED_CROPS if c["id"] == result["crop"]), result["crop"])

# ============================================================== UNCERTAIN
if result.get("uncertain"):
    eyebrow("Step 4 · Diagnosis result")
    st.markdown("## We're not confident enough to call this")

    img_col, msg_col = st.columns([0.42, 0.58], gap="large")
    with img_col:
        st.image(image, use_container_width=True)
        st.markdown(f'<span class="pill">Crop · {crop_label}</span>', unsafe_allow_html=True)

    with msg_col:
        st.markdown(
            f"""
            <div class="warn-banner">
                <strong>Image is ambiguous.</strong> Please upload another clear image
                showing the affected leaf. The model's best guess
                (<strong>{result['disease']}</strong>) fell below our confidence threshold,
                so we're not presenting it as a diagnosis.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            """
            <div class="card tight">
                <div class="eyebrow">Tips for a clearer result</div>
                <ul style="margin-top:0.5rem; color:var(--muted); font-size:0.9rem; line-height:1.7;">
                    <li>Get closer — fill the frame with the affected leaf</li>
                    <li>Use even, natural daylight</li>
                    <li>Avoid blur — hold the camera steady</li>
                    <li>Photograph the leaf against a plain background if possible</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("📷  Retake / Re-upload Image", type="primary"):
            reset_diagnosis()
            st.switch_page("pages/1_🔬_Diagnosis.py")

    st.stop()

# ================================================================ RESULT
eyebrow("Step 4 · Diagnosis result")
st.markdown(f"## {result['disease']}")
st.markdown(
    f'<div style="margin-top:-0.6rem; display:flex; gap:0.6rem; align-items:center;">'
    f'<span class="pill">🌿 {crop_label}</span>{severity_badge(result["severity"])}</div>',
    unsafe_allow_html=True,
)

st.write("")
img_col, data_col = st.columns([0.42, 0.58], gap="large")

with img_col:
    st.markdown('<div class="eyebrow">Analyzed image</div>', unsafe_allow_html=True)
    st.image(image, use_container_width=True)

with data_col:
    st.markdown('<div class="eyebrow">Confidence</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        gauge_card(
            result["disease_confidence"] * 100,
            "DISEASE",
            "Disease prediction confidence",
            color="#2D6A4F",
        )
    with g2:
        severity_color = {"Mild": "#2D6A4F", "Moderate": "#C77D22", "Severe": "#B3261E"}[result["severity"]]
        gauge_card(
            result["severity_confidence"] * 100,
            "SEVERITY",
            "Severity assessment confidence",
            color=severity_color,
        )

    st.write("")
    st.markdown(
        f"""
        <div class="card tight">
            <div class="eyebrow">Severity guide</div>
            <div style="display:flex; gap:0.8rem; margin-top:0.6rem; flex-wrap:wrap;">
                {severity_badge("Mild")} <span style="color:var(--muted); font-size:0.85rem;">
                    Early symptoms, low spread risk
                </span>
            </div>
            <div style="display:flex; gap:0.8rem; margin-top:0.5rem; flex-wrap:wrap;">
                {severity_badge("Moderate")} <span style="color:var(--muted); font-size:0.85rem;">
                    Noticeable damage, action recommended soon
                </span>
            </div>
            <div style="display:flex; gap:0.8rem; margin-top:0.5rem; flex-wrap:wrap;">
                {severity_badge("Severe")} <span style="color:var(--muted); font-size:0.85rem;">
                    Extensive damage, prompt action needed
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

divider()

cta1, cta2, cta3 = st.columns(3)
with cta1:
    if st.button("🤖  Ask the AI Assistant", type="primary", use_container_width=True):
        st.switch_page("pages/3_🤖_Assistant.py")
with cta2:
    if st.button("🔄  Diagnose Another Leaf", type="secondary", use_container_width=True):
        reset_diagnosis()
        st.switch_page("pages/1_🔬_Diagnosis.py")
with cta3:
    if st.button("🏠  Back to Home", type="secondary", use_container_width=True):
        st.switch_page("app.py")

st.markdown(
    '<div class="footer-note">Results are model estimates intended as decision support, '
    "not a substitute for expert agronomic diagnosis.</div>",
    unsafe_allow_html=True,
)
