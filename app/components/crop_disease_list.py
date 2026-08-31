"""
Crop disease reference list — shows farmers all detectable diseases per crop.
"""

import streamlit as st

from data.crops import SUPPORTED_CROPS, DISEASE_CLASSES
from chatbot.disease_knowledge import get_disease_info


def _disease_key(crop_id: str, disease_name: str) -> str:
    return f"{crop_id}_{disease_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"


def _disease_pills(crop_id: str, diseases: list[str]) -> str:
    pills_html = ""
    for disease in diseases:
        if disease == "Healthy":
            pills_html += (
                '<span style="display:inline-flex; align-items:center; gap:0.3rem;'
                "font-size:0.78rem; font-weight:600; padding:0.3rem 0.65rem;"
                "border-radius:999px; background:#EAF3EC; color:#1B4332;"
                f'margin:0.2rem 0.15rem;">✓ {disease}</span>'
            )
            continue

        info = get_disease_info(crop_id, disease)
        tooltip = ""
        if info:
            symptom_summary = info["symptoms"][0] if info["symptoms"] else ""
            pathogen = info.get("pathogen", "")
            tooltip = f"{pathogen} — {symptom_summary}" if symptom_summary else pathogen

        title_attr = f' title="{tooltip}"' if tooltip else ""
        pills_html += (
            f'<span{title_attr} style="display:inline-flex; align-items:center;'
            "gap:0.3rem; font-size:0.78rem; font-weight:600;"
            "padding:0.3rem 0.65rem; border-radius:999px;"
            "background:#FBF1E1; color:#7A4E15;"
            f'margin:0.2rem 0.15rem; cursor:help;">{disease}</span>'
        )
    return pills_html


def render_crop_disease_list():
    """Render an expandable list of all detectable diseases per crop."""
    st.markdown(
        '<div style="margin-top:2.5rem;">'
        '<div class="eyebrow">Reference</div>'
        '<h3 style="margin-top:0.3rem;">Detectable diseases by crop</h3>'
        '<p style="color:var(--muted); font-size:0.9rem; margin-top:-0.3rem;">'
        "All diseases our AI model can identify for each crop. "
        "Hover over a disease name for a quick summary."
        "</p></div>",
        unsafe_allow_html=True,
    )

    for crop in SUPPORTED_CROPS:
        crop_id = crop["id"]
        diseases = DISEASE_CLASSES.get(crop_id, [])
        disease_count = len([d for d in diseases if d != "Healthy"])

        with st.expander(
            f"{crop['emoji']}  {crop['label']}  —  {disease_count} detectable disease{'s' if disease_count != 1 else ''}",
            expanded=(st.session_state.get("selected_crop") == crop_id),
        ):
            st.markdown(
                f'<div style="margin-bottom:0.6rem;">{_disease_pills(crop_id, diseases)}</div>',
                unsafe_allow_html=True,
            )

            detail_rows = ""
            for disease in diseases:
                if disease == "Healthy":
                    continue
                info = get_disease_info(crop_id, disease)
                if info:
                    pathogen = info.get("pathogen", "—")
                    top_treatment = info["treatment_organic"][0] if info["treatment_organic"] else "—"
                    detail_rows += (
                        f"<tr>"
                        f"<td style='font-weight:600; padding:0.5rem 0.7rem; border-bottom:1px solid #EFEEE6;'>{disease}</td>"
                        f"<td style='padding:0.5rem 0.7rem; border-bottom:1px solid #EFEEE6; color:var(--muted); font-size:0.85rem;'>{pathogen}</td>"
                        f"<td style='padding:0.5rem 0.7rem; border-bottom:1px solid #EFEEE6; font-size:0.85rem;'>{top_treatment}</td>"
                        f"</tr>"
                    )

            if detail_rows:
                st.markdown(
                    f"""
                    <div style="overflow-x:auto; margin-top:0.5rem;">
                    <table style="width:100%; border-collapse:collapse; font-size:0.88rem;">
                        <thead>
                            <tr style="background:var(--surface-alt);">
                                <th style="text-align:left; padding:0.5rem 0.7rem; font-weight:700; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; color:var(--muted);">Disease</th>
                                <th style="text-align:left; padding:0.5rem 0.7rem; font-weight:700; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; color:var(--muted);">Pathogen</th>
                                <th style="text-align:left; padding:0.5rem 0.7rem; font-weight:700; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; color:var(--muted);">First-line treatment</th>
                            </tr>
                        </thead>
                        <tbody>{detail_rows}</tbody>
                    </table>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("Detailed information not yet available for this crop.")
