"""
Kisan Dost (کسان دوست) — the farming assistant chatbot widget.
Lives in the sidebar as the primary conversational interface.
"""

import streamlit as st

CHATBOT_NAME = "Kisan Dost"
CHATBOT_URDU = "کسان دوست"
CHATBOT_TAGLINE = "Your farming companion"


def _get_chatbot():
    """Lazy-import the chatbot engine. Returns (ask_fn, error_msg)."""
    try:
        from chatbot.plantcare_ai import ask
        return ask, None
    except Exception as e:
        return None, str(e)


def render_sidebar_chatbot():
    """Render Kisan Dost in the sidebar."""

    if "sidebar_chat_history" not in st.session_state:
        st.session_state.sidebar_chat_history = []

    result = st.session_state.get("diagnosis_result")
    context = result if result and not result.get("uncertain") else {}

    ask_fn, chat_error = _get_chatbot()

    with st.sidebar:
        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.1);margin:1rem 0;"></div>',
            unsafe_allow_html=True,
        )

        # ── Kisan Dost header ──
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:0.15rem;">
                <div style="width:36px;height:36px;border-radius:50%;
                            background:linear-gradient(135deg, #2D6A4F, #74A57F);
                            display:flex;align-items:center;justify-content:center;
                            font-size:1.1rem;flex-shrink:0;">
                    🌱
                </div>
                <div>
                    <div style="font-family:'Fraunces',serif;font-size:1.05rem;
                                font-weight:600;color:#FFFFFF;line-height:1.2;">
                        {CHATBOT_NAME}
                    </div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.58rem;
                                letter-spacing:0.08em;color:rgba(255,255,255,0.45);
                                text-transform:uppercase;">
                        {CHATBOT_URDU} · {CHATBOT_TAGLINE}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if context and context.get("disease"):
            crop_label = context.get("crop", "Unknown")
            disease_label = context.get("disease", "")
            st.markdown(
                f'<div style="background:rgba(116,165,127,0.15);border:1px solid rgba(116,165,127,0.3);'
                f'border-radius:8px;padding:0.45rem 0.65rem;font-size:0.78rem;color:#C9DCC5;margin-top:0.4rem;">'
                f'🔍 Looking at: <strong>{crop_label} — {disease_label}</strong></div>',
                unsafe_allow_html=True,
            )

        # ── Play pending voice response ──
        pending_audio = st.session_state.pop("pending_voice_bytes", None)
        if pending_audio:
            st.audio(pending_audio, format='audio/mp3')

        # ── Chat messages ──
        history = st.session_state.sidebar_chat_history

        if history:
            chat_container = st.container(height=320)
            with chat_container:
                for turn in history:
                    if turn["role"] == "user":
                        st.markdown(
                            f'<div style="background:rgba(255,255,255,0.08);border-radius:10px 10px 2px 10px;'
                            f'padding:0.5rem 0.7rem;margin-bottom:0.4rem;font-size:0.85rem;">'
                            f'{turn["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="background:rgba(45,106,79,0.25);border:1px solid rgba(116,165,127,0.2);'
                            f'border-radius:10px 10px 10px 2px;padding:0.5rem 0.7rem;margin-bottom:0.4rem;'
                            f'font-size:0.85rem;color:#C9DCC5;">'
                            f'🌱 {turn["content"]}</div>',
                            unsafe_allow_html=True,
                        )
        else:
            st.markdown(
                '<div style="text-align:center;padding:1.2rem 0.5rem;color:rgba(255,255,255,0.5);font-size:0.82rem;">'
                '<div style="font-size:1.6rem;margin-bottom:0.4rem;">🌾</div>'
                'Ask me about diseases, treatments,<br>or crop care tips.'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Quick suggestions ──
        if not history:
            cols = st.columns(2)
            suggestions = ["How to treat?", "Prevention tips", "Organic remedies", "What is it?"]
            for i, suggestion in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(suggestion, key=f"quick_{i}", use_container_width=True):
                        st.session_state.sidebar_chat_history.append({
                            "role": "user", "content": suggestion
                        })
                        st.session_state["pending_quick_ask"] = suggestion
                        st.rerun()

        # ── Input form ──
        with st.form(key="sidebar_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask Kisan Dost:",
                key="sidebar_chat_input",
                placeholder="Type your question...",
                label_visibility="collapsed",
            )
            submit = st.form_submit_button("Send", use_container_width=True)

            if submit and user_input:
                st.session_state.sidebar_chat_history.append({
                    "role": "user", "content": user_input
                })
                st.session_state["pending_quick_ask"] = user_input
                st.rerun()

        # ── Voice input ──
        from app.components.voice import render_voice_input_button
        render_voice_input_button(
            placeholder="Type your question...",
            key="sidebar_voice",
            auto_submit=True,
        )

        # ── Process pending question ──
        pending = st.session_state.pop("pending_quick_ask", None)
        if pending and ask_fn:
            with st.spinner("Thinking..."):
                try:
                    reply = ask_fn(pending, context, st.session_state.sidebar_chat_history)
                except Exception as e:
                    reply = f"Sorry, something went wrong: {str(e)}"
            st.session_state.sidebar_chat_history.append({
                "role": "assistant", "content": reply
            })
            # Store voice audio for next render cycle (before rerun)
            if st.session_state.get("voice_output_enabled", False):
                try:
                    from app.components.voice import text_to_speech_urdu
                    audio_bytes = text_to_speech_urdu(reply)
                    if audio_bytes:
                        st.session_state["pending_voice_bytes"] = audio_bytes
                except Exception:
                    pass
            st.rerun()
        elif pending and chat_error:
            st.session_state.sidebar_chat_history.append({
                "role": "assistant",
                "content": "Chatbot is loading. Please try again in a moment."
            })
            st.rerun()

        # ── Voice output toggle ──
        if "voice_output_enabled" not in st.session_state:
            st.session_state.voice_output_enabled = False

        voice_col1, voice_col2 = st.columns([2, 1])
        with voice_col1:
            st.markdown(
                '<div style="font-size:0.72rem; color:rgba(255,255,255,0.5);">🔊 Urdu voice</div>',
                unsafe_allow_html=True,
            )
        with voice_col2:
            toggle_val = st.toggle("Voice", key="voice_toggle_sidebar", label_visibility="collapsed")
            st.session_state.voice_output_enabled = toggle_val

        # ── Footer actions ──
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear", key="clear_sidebar_chat", use_container_width=True):
                st.session_state.sidebar_chat_history = []
                st.rerun()
