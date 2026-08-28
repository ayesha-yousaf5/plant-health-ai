import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.styles.theme import inject_theme
from app.components.nav import render_sidebar
from app.components.state import init_state
from app.components.ui import eyebrow, divider
from data.crops import SUPPORTED_CROPS

st.set_page_config(page_title="About · Plant Health AI", page_icon="ℹ️", layout="wide")

init_state()
inject_theme()
render_sidebar(active="about")

eyebrow("About the project")
st.markdown("## Plant Disease Detection & Severity Assessment")
st.markdown(
    """
    <p style="color:var(--muted); max-width:640px;">
    Plant Health AI turns a single leaf photograph into a disease diagnosis,
    a confidence score, and a severity read-out, followed by grounded
    management guidance from an AI assistant. It's built for fast,
    low-friction use by farmers and agronomists in the field — no
    specialized equipment beyond a phone camera.
    </p>
    """,
    unsafe_allow_html=True,
)

divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Supported crops")
    for crop in SUPPORTED_CROPS:
        st.markdown(f"- {crop['emoji']} **{crop['label']}** — {crop['blurb']}")

with col2:
    st.markdown("### Dataset")
    st.markdown(
        """
        The disease and severity models are being trained on
        **PlantInquiryVQA**, a visual-question-answering dataset covering
        crop leaf imagery paired with disease and condition annotations.

        For this hackathon build, the interface runs on a **mock prediction
        layer** with the exact same output structure the trained model will
        return, so no UI changes are needed at integration time.
        """
    )

divider()

st.markdown("### Methodology")
st.markdown(
    """
    1. **Crop selection** narrows the disease vocabulary the model
       reasons over, improving prediction quality.
    2. **Disease classification** produces a predicted disease label and
       a confidence score from the leaf image.
    3. **Severity assessment** runs only when the disease prediction is
       confident, and returns a **Mild / Moderate / Severe** rating —
       exact infected-area percentages are intentionally not shown to
       keep the result easy to act on.
    4. **Uncertainty handling**: predictions below the confidence
       threshold are never shown as a definite diagnosis — the user is
       asked for a clearer photo instead.
    5. **AI assistant**: a chat interface grounded in the diagnosis result
       gives general management guidance, not an exact treatment
       prescription.
    """
)

divider()

st.markdown("### System limitations")
st.markdown(
    """
    - Predictions are estimates from a machine-learning model and can be
      wrong, especially on poor-quality or unusual images.
    - The current build uses **mock predictions**; real model accuracy
      will depend on final training results on PlantInquiryVQA.
    - Coverage is limited to the crops and diseases listed above.
    - Severity is a coarse three-tier estimate, not a lab-grade
      quantitative assessment.
    - The assistant provides general guidance, not region-specific
      regulatory or product-label advice.
    """
)

st.markdown(
    """
    <div class="card tight" style="margin-top:1rem;">
        <strong>Disclaimer:</strong> Plant Health AI is a decision-support
        tool, not a substitute for a qualified agronomist or local
        agricultural extension service. Always verify significant
        treatment decisions, especially product choice and dosage, with a
        qualified professional before acting.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
if st.button("🔬  Start Diagnosis", type="primary"):
    st.switch_page("pages/1_🔬_Diagnosis.py")
