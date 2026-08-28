import streamlit as st
from data.crops import SUPPORTED_CROPS


def _crop_label(crop_id):
    for c in SUPPORTED_CROPS:
        if c["id"] == crop_id:
            return f'{c["emoji"]} {c["label"]}'
    return None


def render_sidebar(active: str = ""):
    """Renders the persistent left navigation + live diagnosis context.

    `active` is just used to bold/mark the current page name in the caption;
    actual navigation between pages is handled by Streamlit's native
    multipage router (the pages/ folder), we only add a friendlier visual
    wrapper and a context summary on top of it.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.2rem;">
                <span style="font-size:1.4rem;">🌿</span>
                <span style="font-family:'Fraunces',serif;font-size:1.15rem;font-weight:600;color:#FFFFFF;">
                    Plant Health AI
                </span>
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                        letter-spacing:0.08em;color:rgba(255,255,255,0.55);
                        text-transform:uppercase;margin-bottom:1.4rem;">
                Diagnosis & Severity Assistant
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link("app.py", label="Home", icon="🏠")
        st.page_link("pages/1_🔬_Diagnosis.py", label="Diagnosis", icon="🔬")
        st.page_link("pages/2_📊_Results.py", label="Results", icon="📊")
        st.page_link("pages/3_🤖_Assistant.py", label="AI Assistant", icon="🤖")
        st.page_link("pages/4_ℹ️_About.py", label="About", icon="ℹ️")

        st.markdown('<div style="height:1px;background:rgba(255,255,255,0.14);margin:1.2rem 0;"></div>',
                     unsafe_allow_html=True)

        crop = st.session_state.get("selected_crop")
        result = st.session_state.get("diagnosis_result")

        st.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.68rem;'
            'letter-spacing:0.08em;color:rgba(255,255,255,0.55);text-transform:uppercase;'
            'margin-bottom:0.5rem;">Current Session</div>',
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
