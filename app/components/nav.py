"""
Unified sidebar — navigation + Krishi Mitra chatbot in one clean panel.
"""

import streamlit as st
from data.crops import SUPPORTED_CROPS


def _crop_label(crop_id):
    for c in SUPPORTED_CROPS:
        if c["id"] == crop_id:
            return f'{c["emoji"]} {c["label"]}'
    return None


def render_sidebar(active: str = ""):
    """Renders the unified sidebar with nav + Krishi Mitra chatbot."""

    with st.sidebar:
        # ── Brand ──
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.15rem;">
                <span style="font-size:1.6rem;">🌿</span>
                <div>
                    <div style="font-family:'Fraunces',serif;font-size:1.2rem;font-weight:600;color:#FFFFFF;line-height:1.2;">
                        Plant Health AI
                    </div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;
                                letter-spacing:0.1em;color:rgba(255,255,255,0.45);
                                text-transform:uppercase;">
                        Smart Crop Diagnosis
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.1);margin:1rem 0;"></div>',
            unsafe_allow_html=True,
        )

        # ── Navigation ──
        st.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;'
            'letter-spacing:0.1em;color:rgba(255,255,255,0.4);text-transform:uppercase;'
            'margin-bottom:0.5rem;">Navigate</div>',
            unsafe_allow_html=True,
        )

        st.page_link("app.py", label="Home", icon="🏠")
        st.page_link("pages/1_🔬_Diagnosis.py", label="Diagnosis", icon="🔬")
        st.page_link("pages/2_📊_Results.py", label="Results", icon="📊")
        st.page_link("pages/4_ℹ️_About.py", label="About", icon="ℹ️")

        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.1);margin:1rem 0;"></div>',
            unsafe_allow_html=True,
        )

        # ── Session context ──
        crop = st.session_state.get("selected_crop")
        result = st.session_state.get("diagnosis_result")

        st.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;'
            'letter-spacing:0.1em;color:rgba(255,255,255,0.4);text-transform:uppercase;'
            'margin-bottom:0.5rem;">Session</div>',
            unsafe_allow_html=True,
        )

        if crop:
            st.markdown(f"**Crop:** {_crop_label(crop)}")
        else:
            st.caption("No crop selected yet")

        if result:
            if result.get("uncertain"):
                st.markdown("**Status:** :orange[Needs clearer image]")
            else:
                st.markdown(f"**Disease:** {result['disease']}")
                st.markdown(f"**Severity:** {result['severity']}")
        else:
            st.caption("No diagnosis yet")
