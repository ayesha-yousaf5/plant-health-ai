"""
Voice system for Krishi Mitra — Hindi speech input and output.
"""

import streamlit as st
import os
import tempfile
from pathlib import Path


def _check_gtts():
    """Check if gTTS is available."""
    try:
        from gtts import gTTS
        return True
    except ImportError:
        return False


def text_to_speech_hindi(text: str) -> bytes | None:
    """Convert text to Hindi speech audio using gTTS.
    
    Returns audio bytes or None if gTTS is not available.
    """
    if not _check_gtts():
        return None
    
    try:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='hi', slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            fp_path = fp.name
        
        with open(fp_path, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(fp_path)
        return audio_bytes
    
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")
        return None


def render_voice_input_button(key: str = "voice_input") -> str | None:
    """Render a voice input button that captures Hindi speech.
    
    Returns the transcribed text or None.
    Uses the browser's Web Speech API which supports Hindi.
    """
    
    voice_js = """
    <div style="text-align:center; margin:0.5rem 0;">
        <button id="voiceBtn_{key}" onclick="toggleVoice_{key}()" 
                style="background:linear-gradient(135deg, #2D6A4F, #74A57F);
                       color:white; border:none; border-radius:50%;
                       width:48px; height:48px; font-size:1.3rem;
                       cursor:pointer; box-shadow:0 2px 8px rgba(45,106,79,0.3);
                       transition:all 0.3s ease;">
            🎤
        </button>
        <div id="voiceStatus_{key}" style="font-size:0.75rem; color:var(--muted); margin-top:0.3rem;">
            Click to speak in Hindi
        </div>
    </div>
    
    <script>
    let recognition_{key} = null;
    let isListening_{key} = false;
    
    function toggleVoice_{key}() {{
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
            alert('Speech recognition not supported in this browser. Please use Chrome.');
            return;
        }}
        
        if (isListening_{key}) {{
            stopVoice_{key}();
        }} else {{
            startVoice_{key}();
        }}
    }}
    
    function startVoice_{key}() {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition_{key} = new SpeechRecognition();
        recognition_{key}.lang = 'hi-IN';
        recognition_{key}.continuous = false;
        recognition_{key}.interimResults = false;
        
        recognition_{key}.onstart = function() {{
            isListening_{key} = true;
            document.getElementById('voiceBtn_{key}').style.background = 'linear-gradient(135deg, #B3261E, #dc3545)';
            document.getElementById('voiceBtn_{key}').style.animation = 'pulse 1s infinite';
            document.getElementById('voiceStatus_{key}').textContent = 'Listening... speak now';
            document.getElementById('voiceStatus_{key}').style.color = '#B3261E';
        }};
        
        recognition_{key}.onresult = function(event) {{
            const transcript = event.results[0][0].transcript;
            document.getElementById('voiceStatus_{key}').textContent = 'Heard: ' + transcript;
            document.getElementById('voiceStatus_{key}').style.color = 'var(--forest-500)';
            
            // Store in a hidden input that Streamlit can read
            const input = document.createElement('input');
            input.type = 'hidden';
            input.id = 'voiceResult_{key}';
            input.value = transcript;
            document.body.appendChild(input);
            
            // Trigger Streamlit rerun
            setTimeout(() => {{
                window.parent.document.querySelector('[data-testid="stApp"]')
                    .dispatchEvent(new Event('voiceInputReceived'));
            }}, 100);
        }};
        
        recognition_{key}.onerror = function(event) {{
            document.getElementById('voiceStatus_{key}').textContent = 'Error: ' + event.error;
            document.getElementById('voiceStatus_{key}').style.color = '#B3261E';
            stopVoice_{key}();
        }};
        
        recognition_{key}.onend = function() {{
            stopVoice_{key}();
        }};
        
        recognition_{key}.start();
    }}
    
    function stopVoice_{key}() {{
        if (recognition_{key}) {{
            recognition_{key}.stop();
        }}
        isListening_{key} = false;
        document.getElementById('voiceBtn_{key}').style.background = 'linear-gradient(135deg, #2D6A4F, #74A57F)';
        document.getElementById('voiceBtn_{key}').style.animation = '';
    }}
    </script>
    """.replace("{key}", key)
    
    st.markdown(voice_js, unsafe_allow_html=True)
    
    # Check if voice input was received (this is a simplified version)
    # In practice, you'd need to use streamlit-javascript or similar to read the result
    return None


def render_voice_output_toggle():
    """Render a toggle for voice output."""
    if "voice_output_enabled" not in st.session_state:
        st.session_state.voice_output_enabled = False
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            '<div style="font-size:0.85rem; color:var(--muted);">🔊 Voice output (Hindi)</div>',
            unsafe_allow_html=True,
        )
    with col2:
        if st.toggle("Enable", key="voice_toggle", label_visibility="collapsed"):
            st.session_state.voice_output_enabled = True
        else:
            st.session_state.voice_output_enabled = False


def speak_hindi(text: str):
    """Speak text in Hindi if voice output is enabled."""
    if not st.session_state.get("voice_output_enabled", False):
        return
    
    audio_bytes = text_to_speech_hindi(text)
    if audio_bytes:
        st.audio(audio_bytes, format='audio/mp3')
