"""
Single source of truth for st.session_state keys used across pages.

Keeping this in one place avoids typos like st.session_state["crop"] in one
file and st.session_state["selected_crop"] in another, which is the #1
source of bugs in multipage Streamlit apps.
"""

import streamlit as st

DEFAULTS = {
    "selected_crop": None,       # str | None  e.g. "tomato"
    "uploaded_image": None,      # PIL.Image | None
    "image_source": None,        # "upload" | "camera" | None
    "diagnosis_result": None,    # dict | None  (see models/predictor.py schema)
    "chat_history": [],          # list[dict(role, content)]
    "diagnosis_running": False,  # bool, drives the loading state
}


def init_state():
    """Ensure every expected key exists. Safe to call on every page load."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            # lists/dicts must be fresh objects per session, not shared refs
            st.session_state[key] = default if not isinstance(default, (list, dict)) else type(default)()


def reset_diagnosis():
    """Called when the user wants to start over / re-upload an image."""
    st.session_state["uploaded_image"] = None
    st.session_state["image_source"] = None
    st.session_state["diagnosis_result"] = None
    st.session_state["diagnosis_running"] = False


def reset_all():
    reset_diagnosis()
    st.session_state["selected_crop"] = None
    st.session_state["chat_history"] = []
