"""
Voice system for Kisan Dost — Urdu speech input and output.
"""

import asyncio
import json
import os
import re
import tempfile

import streamlit as st
import streamlit.components.v1 as components


def _check_edge_tts():
    try:
        import edge_tts  # noqa: F401
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


URDU_VOICE = "ur-PK-UzmaNeural"


def text_to_speech_urdu(text: str) -> bytes | None:
    """Convert text to Urdu speech audio using Edge TTS (Microsoft neural voice).

    Returns audio bytes (MP3) or None on failure.
    """
    if not _check_edge_tts():
        return None

    clean_text = _strip_markdown(text)
    if not clean_text:
        return None

    try:
        import edge_tts

        async def _synthesize():
            communicate = edge_tts.Communicate(clean_text, URDU_VOICE)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                tmp_path = fp.name
            await communicate.save(tmp_path)
            with open(tmp_path, 'rb') as f:
                audio = f.read()
            os.unlink(tmp_path)
            return audio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                audio_bytes = pool.submit(asyncio.run, _synthesize()).result()
        else:
            audio_bytes = asyncio.run(_synthesize())

        return audio_bytes

    except Exception:
        return None


def speak_if_enabled(text: str):
    """Render Urdu audio if voice output is enabled. Safe to call before rerun."""
    if not st.session_state.get("voice_output_enabled", False):
        return
    audio_bytes = text_to_speech_urdu(text)
    if audio_bytes:
        st.audio(audio_bytes, format='audio/mp3')


def render_voice_input_button(placeholder: str, key: str = "voice_input",
                               auto_submit: bool = True):
    """Render a mic button that captures Urdu speech and fills a text input.

    Uses ``streamlit.components.v1.html()`` so the ``<script>`` actually
    executes (``st.markdown`` injects via innerHTML which skips scripts).
    The component runs in a same-origin iframe; speech recognition happens
    inside the iframe and the transcript is bridged to the parent document's
    text input via the native value-setter trick.

    Args:
        placeholder: The placeholder text of the target Streamlit text input
                     or chat_input element.
        key: Unique suffix for DOM ids and JS function names.
        auto_submit: If True, auto-submit the form / press Enter after
                     transcription so the user doesn't have to click Send.
    """
    ph_json = json.dumps(placeholder)
    auto_js = "true" if auto_submit else "false"

    voice_html = f"""
    <html>
    <head>
    <style>
        body {{ margin:0; padding:0; background:transparent; }}
        @keyframes voicePulse_{key} {{
            0%,100% {{ transform:scale(1); }}
            50% {{ transform:scale(1.12); }}
        }}
        #voiceBtn_{key} {{
            background:linear-gradient(135deg,#2D6A4F,#74A57F);
            color:white; border:none; border-radius:50%;
            width:36px; height:36px; font-size:1rem;
            cursor:pointer; box-shadow:0 2px 6px rgba(45,106,79,0.3);
            transition:all 0.2s ease; line-height:1;
        }}
        #voiceBtn_{key}.listening {{
            background:linear-gradient(135deg,#B3261E,#dc3545) !important;
            animation:voicePulse_{key} 1s infinite;
        }}
    </style>
    </head>
    <body>
    <div style="display:inline-flex;align-items:center;gap:0.5rem;">
        <button onclick="toggleVoice()" id="voiceBtn_{key}"
                title="Click to speak in Urdu">
            🎤
        </button>
        <span id="voiceStatus_{key}"
              style="font-size:0.72rem;color:rgba(255,255,255,0.5);">
            Click to speak
        </span>
    </div>

    <script>
    (function() {{
        var PH = {ph_json};
        var AUTO = {auto_js};
        var parentDoc = window.parent.document;

        window.toggleVoice = function() {{
            var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SR) {{
                alert('Speech recognition not supported. Please use Chrome or Edge.');
                return;
            }}

            var btn = document.getElementById('voiceBtn_{key}');
            var status = document.getElementById('voiceStatus_{key}');
            var recognition = new SR();
            recognition.lang = 'ur-PK';
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = function() {{
                btn.classList.add('listening');
                status.textContent = 'Listening...';
                status.style.color = '#B3261E';
            }};

            recognition.onresult = function(event) {{
                var transcript = event.results[0][0].transcript;
                status.textContent = transcript;
                status.style.color = '#2D6A4F';

                var target = null;
                var inputs = parentDoc.querySelectorAll('input[type="text"]');
                for (var i = 0; i < inputs.length; i++) {{
                    if (inputs[i].placeholder === PH) {{ target = inputs[i]; break; }}
                }}
                if (!target) {{
                    var tas = parentDoc.querySelectorAll('textarea');
                    for (var j = 0; j < tas.length; j++) {{
                        if (tas[j].placeholder === PH) {{ target = tas[j]; break; }}
                    }}
                }}

                if (target) {{
                    var parentWin = window.parent;
                    var proto = target.tagName === 'TEXTAREA'
                        ? parentWin.HTMLTextAreaElement.prototype
                        : parentWin.HTMLInputElement.prototype;
                    var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                    setter.call(target, transcript);
                    target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    target.dispatchEvent(new Event('change', {{ bubbles: true }}));

                    if (AUTO) {{
                        setTimeout(function() {{
                            var form = target.closest('form');
                            if (form) {{
                                var sb = form.querySelector('button[type="submit"]');
                                if (sb) {{ sb.click(); return; }}
                            }}
                            target.dispatchEvent(new KeyboardEvent('keydown', {{
                                key:'Enter', code:'Enter', keyCode:13, bubbles:true
                            }}));
                        }}, 250);
                    }}
                }} else {{
                    status.textContent = 'Input not found';
                    status.style.color = '#C77D22';
                }}

                btn.classList.remove('listening');
            }};

            recognition.onerror = function(event) {{
                status.textContent = 'Error: ' + event.error;
                status.style.color = '#B3261E';
                btn.classList.remove('listening');
            }};

            recognition.onend = function() {{
                btn.classList.remove('listening');
            }};

            recognition.start();
        }};
    }})();
    </script>
    </body>
    </html>
    """

    components.html(voice_html, height=50)
