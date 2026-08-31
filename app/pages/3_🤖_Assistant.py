import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.styles.theme import inject_theme
from app.components.nav import render_sidebar
from app.components.state import init_state
from app.components.ui import eyebrow, divider, severity_badge
from data.crops import SUPPORTED_CROPS

try:
    from chatbot.plantcare_ai import ask
    chatbot_available = True
    chatbot_error = None
except Exception as e:
    chatbot_available = False
    chatbot_error = str(e)

st.set_page_config(page_title="AI Assistant · Plant Health AI", page_icon="🤖", layout="wide")

init_state()
inject_theme()
render_sidebar(active="assistant")

result = st.session_state.get("diagnosis_result")

eyebrow("Step 5")
st.markdown("## Management Guidance Assistant")
st.markdown(
    '<p style="color:var(--muted); margin-top:-0.6rem;">'
    "Ask questions about your diagnosis. Answers are general management "
    "guidance, not an exact treatment prescription."
    "</p>",
    unsafe_allow_html=True,
)
divider()

if not chatbot_available:
    st.error("Chatbot dependencies not available. Please install the required packages:")
    st.code("datasets scikit-learn groq python-dotenv", language="bash")
    st.info(f"Error details: {chatbot_error}")
    st.stop()

if result is None:
    st.info("No diagnosis on file yet — you can still chat, but answers will be general "
             "until you run a diagnosis.")
    if st.button("🔬  Run a Diagnosis First", type="primary"):
        st.switch_page("pages/1_🔬_Diagnosis.py")
    context = {}
elif result.get("uncertain"):
    st.markdown(
        """
        <div class="warn-banner">
            Your last image was flagged as ambiguous, so there's no confirmed
            diagnosis to ground answers in yet. Re-run the diagnosis with a
            clearer photo for specific guidance.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📷  Retake / Re-upload Image", type="primary"):
        st.switch_page("pages/1_🔬_Diagnosis.py")
    context = result
else:
    crop_label = next((c["label"] for c in SUPPORTED_CROPS if c["id"] == result["crop"]), result["crop"])
    st.markdown(
        f"""
        <div class="card tight" style="margin-bottom:1.2rem;">
            <div class="eyebrow">Grounded in your latest diagnosis</div>
            <div style="display:flex; gap:1.6rem; align-items:center; margin-top:0.5rem; flex-wrap:wrap;">
                <div><span class="stat-label">Crop</span><br>
                     <strong>{crop_label}</strong></div>
                <div><span class="stat-label">Disease</span><br>
                     <strong>{result['disease']}</strong></div>
                <div><span class="stat-label">Severity</span><br>
                     {severity_badge(result['severity'])}</div>
                <div><span class="stat-label">Confidence</span><br>
                     <strong>{result['disease_confidence']*100:.0f}%</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    context = result

# --------------------------------------------------------------- CHAT UI
for turn in st.session_state["chat_history"]:
    with st.chat_message(turn["role"], avatar="🌿" if turn["role"] == "assistant" else None):
        st.markdown(turn["content"])

if not st.session_state["chat_history"] and result and not result.get("uncertain"):
    st.markdown(
        '<div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.8rem;">'
        '<span class="pill">Try: "What should I do?"</span>'
        '<span class="pill">Try: "Will it spread?"</span>'
        '<span class="pill">Try: "How confident are you?"</span>'
        "</div>",
        unsafe_allow_html=True,
    )

prompt = st.chat_input("Ask about your diagnosis, e.g. \"What should I do?\"")
if prompt:
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner("Thinking..."):
            reply = ask(prompt, context, st.session_state["chat_history"])
        st.markdown(reply)

    st.session_state["chat_history"].append({"role": "assistant", "content": reply})
