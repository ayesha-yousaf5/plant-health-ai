"""
Reusable presentational components built on raw HTML/SVG injected via
st.markdown(..., unsafe_allow_html=True). Keeping them here means every
page renders results, badges, and gauges identically.
"""

import streamlit as st
import uuid

SEVERITY_BADGE_CLASS = {
    "Mild": "badge-mild",
    "Moderate": "badge-moderate",
    "Severe": "badge-severe",
}

SEVERITY_ICON = {
    "Mild": "●",
    "Moderate": "▲",
    "Severe": "■",
}


def eyebrow(text: str):
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)


def hero(title_html: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-title">{title_html}</div>
            <div class="hero-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def divider():
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    cls = SEVERITY_BADGE_CLASS.get(severity, "badge-mild")
    icon = SEVERITY_ICON.get(severity, "●")
    return f'<span class="badge {cls}">{icon} {severity}</span>'


def stat_block(label: str, value: str):
    st.markdown(
        f"""
        <div>
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def leaf_gauge(percent: float, label: str, color: str = "#2D6A4F", size: int = 108) -> str:
    """
    Returns an <svg> string: a leaf-silhouette gauge that fills bottom-to-top
    proportional to `percent` (0-100). This is the app's signature data
    visual — a confidence meter shaped like the subject matter itself,
    rather than a generic circular/linear progress bar.
    """
    percent = max(0, min(100, percent))
    fill_y = 100 - percent  # svg y grows downward; clip rect starts here
    uid = uuid.uuid4().hex[:8]

    leaf_path = (
        "M50 4 C 20 10, 6 40, 10 66 C 13 86, 30 96, 50 96 "
        "C 70 96, 87 86, 90 66 C 94 40, 80 10, 50 4 Z"
    )

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <clipPath id="clip-{uid}">
          <path d="{leaf_path}" />
        </clipPath>
        <linearGradient id="grad-{uid}" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stop-color="{color}" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="{color}" stop-opacity="0.55"/>
        </linearGradient>
      </defs>
      <path d="{leaf_path}" fill="#EFEEE6" stroke="#DDE3DA" stroke-width="1.5"/>
      <g clip-path="url(#clip-{uid})">
        <rect x="0" y="{fill_y}" width="100" height="{percent}" fill="url(#grad-{uid})">
          <animate attributeName="y" from="100" to="{fill_y}" dur="0.7s" fill="freeze" />
        </rect>
      </g>
      <path d="{leaf_path}" fill="none" stroke="#0F2818" stroke-width="1" stroke-opacity="0.15"/>
      <line x1="50" y1="18" x2="50" y2="88" stroke="#0F2818" stroke-opacity="0.12" stroke-width="1.2"/>
      <text x="50" y="55" text-anchor="middle" font-family="IBM Plex Mono, monospace"
            font-size="19" font-weight="600" fill="#0F2818">{percent:.0f}%</text>
      <text x="50" y="70" text-anchor="middle" font-family="Manrope, sans-serif"
            font-size="8" fill="#3F4A44" letter-spacing="0.5">{label}</text>
    </svg>
    """


def gauge_card(percent: float, label: str, caption: str, color: str = "#2D6A4F"):
    svg = leaf_gauge(percent, label, color)
    st.markdown(
        f"""
        <div class="card tight" style="text-align:center;">
            {svg}
            <div style="font-size:0.78rem;color:var(--muted);margin-top:0.4rem;">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str):
    return f'<span class="pill">{text}</span>'


def crop_grid_css_note():
    # placeholder kept for symmetry / future extension points
    pass
