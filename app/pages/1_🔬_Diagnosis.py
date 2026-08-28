import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from PIL import Image

from app.styles.theme import inject_theme
from app.components.nav import render_sidebar
from app.components.state import init_state, reset_diagnosis
from app.components.ui import eyebrow, divider
from data.crops import SUPPORTED_CROPS
from models.predictor import run_diagnosis

st.set_page_config(page_title="Diagnosis · Plant Health AI", page_icon="🔬", layout="wide")

init_state()
inject_theme()
render_sidebar(active="diagnosis")

eyebrow("Step 1–3")
st.markdown("## Run a diagnosis")
st.markdown(
    '<p style="color:var(--muted); margin-top:-0.6rem;">'
    "Select your crop, then add a clear photo of the affected leaf."
    "</p>",
    unsafe_allow_html=True,
)
divider()

# ------------------------------------------------------------ CROP SELECT
st.markdown("### 1 · Select your crop")

crop_cols = st.columns(4, gap="small")
for i, crop in enumerate(SUPPORTED_CROPS):
    with crop_cols[i % 4]:
        is_selected = st.session_state["selected_crop"] == crop["id"]
        st.markdown(
            f"""
            <div class="crop-card {'selected' if is_selected else ''}">
                <div class="crop-emoji">{crop['emoji']}</div>
                <div class="crop-name">{crop['label']}</div>
                <div class="crop-blurb">{crop['blurb']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        btn_label = "Selected ✓" if is_selected else "Select"
        if st.button(btn_label, key=f"crop_{crop['id']}", use_container_width=True,
                     type="primary" if is_selected else "secondary"):
            st.session_state["selected_crop"] = crop["id"]
            st.rerun()

st.write("")
divider()

# ------------------------------------------------------------ IMAGE INPUT
st.markdown("### 2 · Add a leaf image")

if not st.session_state["selected_crop"]:
    st.info("Select a crop above to unlock image upload.")
else:
    tab_upload, tab_camera = st.tabs(["📁  Upload from gallery", "📷  Use camera"])

    with tab_upload:
        uploaded = st.file_uploader(
            "Upload a clear, well-lit photo of the affected leaf",
            type=["jpg", "jpeg", "png"],
            key="uploader",
        )
        if uploaded is not None:
            st.session_state["uploaded_image"] = Image.open(uploaded).convert("RGB")
            st.session_state["image_source"] = "upload"
            st.session_state["diagnosis_result"] = None

    with tab_camera:
        camera_img = st.camera_input("Capture the affected leaf", key="camera")
        if camera_img is not None:
            st.session_state["uploaded_image"] = Image.open(camera_img).convert("RGB")
            st.session_state["image_source"] = "camera"
            st.session_state["diagnosis_result"] = None

    if st.session_state["uploaded_image"] is not None:
        st.write("")
        prev_col, tip_col = st.columns([0.55, 0.45], gap="large")
        with prev_col:
            st.markdown('<div class="eyebrow">Preview</div>', unsafe_allow_html=True)
            st.image(st.session_state["uploaded_image"], use_container_width=True)
            if st.button("🔄  Remove & choose a different image", type="secondary"):
                reset_diagnosis()
                st.rerun()
        with tip_col:
            st.markdown(
                """
                <div class="card tight">
                    <div class="eyebrow">For best results</div>
                    <ul style="margin-top:0.5rem; color:var(--muted); font-size:0.9rem; line-height:1.7;">
                        <li>Fill the frame with a single leaf</li>
                        <li>Use natural daylight, avoid harsh shadows</li>
                        <li>Keep the camera steady and in focus</li>
                        <li>Photograph the most visibly affected area</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        analyze_disabled = st.session_state["diagnosis_running"]
        if st.button("✨  Analyze Leaf", type="primary", disabled=analyze_disabled, use_container_width=False):
            st.session_state["diagnosis_running"] = True
            st.rerun()

# --------------------------------------------------------- ANALYSIS STATE
if st.session_state["diagnosis_running"]:
    with st.spinner("Analyzing leaf image — checking for disease patterns and severity..."):
        # Simulated latency so the loading state is visible in the demo.
        # Replace this sleep with the real (sync or async) model call time.
        time.sleep(1.6)
        result = run_diagnosis(
            st.session_state["uploaded_image"],
            st.session_state["selected_crop"],
        )
        st.session_state["diagnosis_result"] = result
        st.session_state["diagnosis_running"] = False
    st.switch_page("pages/2_📊_Results.py")
