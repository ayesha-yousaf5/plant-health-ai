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

st.set_page_config(page_title="Krishi Mitra · Plant Health AI", page_icon="🌱", layout="wide")

init_state()
inject_theme()
render_sidebar(active="assistant")

result = st.session_state.get("diagnosis_result")

# ── Hero ──
st.markdown(
    """
    <div style="text-align:center; padding:2rem 0 1rem;">
        <div style="width:64px;height:64px;border-radius:50%;
                    background:linear-gradient(135deg, #2D6A4F, #74A57F);
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:2rem;margin-bottom:0.8rem;">
            🌱
        </div>
        <h1 style="margin:0;font-size:2.2rem;">Krishi Mitra</h1>
        <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;
                  letter-spacing:0.1em;color:var(--muted);text-transform:uppercase;
                  margin-top:0.3rem;">
            कृषि मित्र · Your Farming Companion
        </p>
    </div>
    """,
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

# ── Chat UI ──
for turn in st.session_state["chat_history"]:
    with st.chat_message(turn["role"], avatar="🌱" if turn["role"] == "assistant" else None):
        st.markdown(turn["content"])

if not st.session_state["chat_history"]:
    st.markdown(
        '<div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.8rem;">'
        '<span class="pill">Try: "What should I do?"</span>'
        '<span class="pill">Try: "Organic treatment?"</span>'
        '<span class="pill">Try: "How to prevent?"</span>'
        '<span class="pill">Try: "Will it spread?"</span>'
        "</div>",
        unsafe_allow_html=True,
    )

# Voice output toggle
if "voice_output_enabled" not in st.session_state:
    st.session_state.voice_output_enabled = False

voice_cols = st.columns([5, 1])
with voice_cols[0]:
    st.markdown(
        '<div style="font-size:0.85rem; color:var(--muted);">🔊 Enable Hindi voice output for responses</div>',
        unsafe_allow_html=True,
    )
with voice_cols[1]:
    toggle_val = st.toggle("Voice", key="voice_toggle_fullpage", label_visibility="collapsed")
    st.session_state.voice_output_enabled = toggle_val

from app.components.voice import render_voice_input_button
render_voice_input_button(
    placeholder="Ask Krishi Mitra about your crop...",
    key="assistant_voice",
    auto_submit=True,
)

prompt = st.chat_input("Ask Krishi Mitra about your crop...")
if prompt:
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Krishi Mitra is thinking..."):
            reply = ask(prompt, context, st.session_state["chat_history"])
        st.markdown(reply)
        
        # Voice output in Hindi
        if st.session_state.get("voice_output_enabled", False):
            try:
                from app.components.voice import text_to_speech_hindi
                audio_bytes = text_to_speech_hindi(reply)
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3')
            except Exception:
                pass

    st.session_state["chat_history"].append({"role": "assistant", "content": reply})
