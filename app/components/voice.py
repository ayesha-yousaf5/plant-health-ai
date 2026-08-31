"""
Voice system for Krishi Mitra — Hindi text-to-speech output.
"""

import streamlit as st
import os
import re
import tempfile


def _check_gtts():
    try:
        from gtts import gTTS
        return True
    except ImportError:
        return False


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so TTS reads clean text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def text_to_speech_hindi(text: str) -> bytes | None:
    """Convert text to Hindi speech audio using gTTS.

    Returns audio bytes or None if gTTS is not available.
    """
    if not _check_gtts():
        return None

    clean_text = _strip_markdown(text)
    if not clean_text:
        return None

    try:
        from gtts import gTTS

        tts = gTTS(text=clean_text, lang='hi', slow=False)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            fp_path = fp.name

        with open(fp_path, 'rb') as f:
            audio_bytes = f.read()

        os.unlink(fp_path)
        return audio_bytes

    except Exception:
        return None


def speak_if_enabled(text: str):
    """Render Hindi audio if voice output is enabled. Safe to call before rerun."""
    if not st.session_state.get("voice_output_enabled", False):
        return
    audio_bytes = text_to_speech_hindi(text)
    if audio_bytes:
        st.audio(audio_bytes, format='audio/mp3')
