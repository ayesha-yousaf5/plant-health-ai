"""
Central design-token system for the app.

Every page calls `inject_theme()` once at the top. Keeping all CSS in one
string (rather than scattered st.markdown calls) means the visual identity
stays consistent as new pages are added, and a future re-skin only touches
this file.

Token summary
-------------
Color:
    --forest-900  #0F2818   deepest ink-green, headings on light bg
    --forest-700  #1B4332   primary brand green (buttons, active nav)
    --forest-500  #2D6A4F   mid green, links/icons
    --leaf-400    #74A57F   supporting green, borders/dividers
    --leaf-200    #C9DCC5   pale green, chips/backgrounds
    --paper       #F7F6F1   app background (warm off-white, not cream-cliché)
    --surface     #FFFFFF   card background
    --surface-alt #EFEEE6   secondary surface / hover
    --ink         #1A1F1B   primary text
    --muted       #63706A   secondary text
    --gold        #D9A441   accent for confidence/CTA highlights (harvest gold,
                             deliberately NOT the terracotta AI-cliche)
    --danger      #B3261E   uncertain / severe warnings
    --warning     #C77D22   moderate severity

Type:
    Display -> 'Fraunces'      (characterful serif, headlines only)
    Body    -> 'Manrope'       (clean humanist sans, everything else)
    Mono    -> 'IBM Plex Mono' (confidence %, data readouts)

Signature element:
    The "leaf gauge" - an SVG leaf silhouette that fills bottom-to-top to
    represent confidence/severity, tying the AI-data language (a gauge) to
    the plant subject matter instead of a generic progress bar.
"""

import streamlit as st

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root{
  --forest-900:#0F2818;
  --forest-700:#1B4332;
  --forest-500:#2D6A4F;
  --leaf-400:#74A57F;
  --leaf-200:#C9DCC5;
  --paper:#F7F6F1;
  --surface:#FFFFFF;
  --surface-alt:#EFEEE6;
  --ink:#1A1F1B;
  --muted:#63706A;
  --gold:#D9A441;
  --danger:#B3261E;
  --danger-bg:#FBEAE8;
  --warning:#C77D22;
  --warning-bg:#FBF1E1;
  --success-bg:#EAF3EC;
  --radius-lg:20px;
  --radius-md:14px;
  --radius-sm:9px;
  --shadow-card: 0 1px 2px rgba(15,40,24,0.04), 0 8px 24px -12px rgba(15,40,24,0.18);
  --shadow-card-hover: 0 4px 8px rgba(15,40,24,0.06), 0 16px 32px -12px rgba(15,40,24,0.24);
}

html, body, [class*="css"]{
  font-family:'Manrope', -apple-system, sans-serif;
  color:var(--ink);
}

.stApp{
  background:
    radial-gradient(ellipse 900px 500px at 8% -10%, rgba(116,165,127,0.14), transparent 60%),
    var(--paper);
}

/* Hide default Streamlit chrome for a cleaner "real product" feel */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:2.2rem; padding-bottom:4rem; max-width:1080px;}

h1,h2,h3{
  font-family:'Fraunces', Georgia, serif;
  color:var(--forest-900);
  letter-spacing:-0.01em;
  line-height:1.12;
}
h1{font-weight:600;}
h2{font-weight:600;}
h3{font-weight:500;}

p, li, span, label, .stMarkdown{
  color:var(--ink);
}

::selection{background:var(--leaf-200); color:var(--forest-900);}

a{color:var(--forest-500);}

/* ---------- Buttons ---------- */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button{
  font-family:'Manrope', sans-serif;
  font-weight:700;
  font-size:0.96rem;
  background:var(--forest-700);
  color:#FFFFFF;
  border:1px solid var(--forest-700);
  border-radius:999px;
  padding:0.62rem 1.6rem;
  transition:transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
  box-shadow:0 1px 2px rgba(15,40,24,0.12);
}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover{
  background:var(--forest-900);
  border-color:var(--forest-900);
  transform:translateY(-1px);
  box-shadow:0 8px 20px -8px rgba(15,40,24,0.45);
  color:#FFFFFF;
}
.stButton>button:active{transform:translateY(0px);}

/* Secondary / ghost button variant via data attribute set from Python */
button[kind="secondary"]{
  background:transparent !important;
  color:var(--forest-700) !important;
  border:1.5px solid var(--leaf-400) !important;
}
button[kind="secondary"]:hover{
  background:var(--surface-alt) !important;
  border-color:var(--forest-500) !important;
  color:var(--forest-900) !important;
}

/* ---------- Inputs ---------- */
.stSelectbox [data-baseweb="select"]>div, .stTextInput input, .stTextArea textarea{
  border-radius:var(--radius-sm) !important;
  border-color:#DDE3DA !important;
  font-family:'Manrope', sans-serif;
}
[data-testid="stFileUploaderDropzone"]{
  background:var(--surface);
  border:1.5px dashed var(--leaf-400);
  border-radius:var(--radius-md);
}
[data-testid="stCameraInput"] video{border-radius:var(--radius-md);}

/* ---------- Sidebar / nav ---------- */
section[data-testid="stSidebar"]{
  background:var(--forest-900);
  border-right:none;
}
section[data-testid="stSidebar"] *{color:#EFF4F0 !important;}
section[data-testid="stSidebar"] .stButton>button{
  background:rgba(255,255,255,0.06);
  border:1px solid rgba(255,255,255,0.14);
  width:100%;
  text-align:left;
  border-radius:var(--radius-sm);
  font-weight:600;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:var(--forest-700);
  border-color:var(--forest-700);
}

/* ---------- Custom components (built with raw HTML via st.markdown) ---------- */

.eyebrow{
  font-family:'IBM Plex Mono', monospace;
  font-size:0.72rem;
  letter-spacing:0.14em;
  text-transform:uppercase;
  color:var(--forest-500);
  font-weight:600;
}

.pill{
  display:inline-flex; align-items:center; gap:0.4rem;
  font-family:'IBM Plex Mono', monospace;
  font-size:0.74rem; font-weight:600; letter-spacing:0.02em;
  padding:0.3rem 0.7rem; border-radius:999px;
  background:var(--leaf-200); color:var(--forest-900);
}

.card{
  background:var(--surface);
  border:1px solid rgba(15,40,24,0.06);
  border-radius:var(--radius-lg);
  padding:1.5rem 1.6rem;
  box-shadow:var(--shadow-card);
  transition:box-shadow 0.2s ease, transform 0.2s ease;
}
.card:hover{box-shadow:var(--shadow-card-hover);}
.card.tight{padding:1.1rem 1.2rem;}

.crop-card{
  background:var(--surface);
  border:1.5px solid rgba(15,40,24,0.07);
  border-radius:var(--radius-md);
  padding:1.1rem 1rem;
  text-align:center;
  transition:all 0.15s ease;
  cursor:pointer;
}
.crop-card:hover{border-color:var(--leaf-400); transform:translateY(-2px); box-shadow:var(--shadow-card);}
.crop-card.selected{
  border-color:var(--forest-700);
  background:var(--success-bg);
  box-shadow:0 0 0 3px rgba(45,106,79,0.12);
}
.crop-emoji{font-size:1.9rem; line-height:1;}
.crop-name{font-weight:700; font-size:0.92rem; margin-top:0.35rem; color:var(--forest-900);}
.crop-blurb{font-size:0.74rem; color:var(--muted); margin-top:0.15rem;}

.badge{
  display:inline-flex; align-items:center; gap:0.35rem;
  font-weight:700; font-size:0.82rem;
  padding:0.32rem 0.75rem; border-radius:999px;
}
.badge-mild{background:var(--success-bg); color:var(--forest-700);}
.badge-moderate{background:var(--warning-bg); color:var(--warning);}
.badge-severe{background:var(--danger-bg); color:var(--danger);}

.stat-label{
  font-family:'IBM Plex Mono', monospace;
  font-size:0.72rem; letter-spacing:0.06em; text-transform:uppercase;
  color:var(--muted); font-weight:600;
}
.stat-value{
  font-family:'Fraunces', serif;
  font-size:1.65rem; font-weight:600; color:var(--forest-900);
  line-height:1.15;
}

.hero-wrap{
  padding:3.2rem 0 1.6rem 0;
}
.hero-title{
  font-family:'Fraunces', serif;
  font-size:clamp(2.1rem, 5vw, 3.4rem);
  font-weight:600;
  color:var(--forest-900);
  line-height:1.06;
  letter-spacing:-0.015em;
  margin-bottom:0.9rem;
}
.hero-sub{
  font-size:1.08rem;
  color:var(--muted);
  max-width:560px;
  line-height:1.55;
}
.hero-accent{color:var(--forest-500); font-style:italic;}

.divider-line{
  height:1px;
  background:linear-gradient(90deg, rgba(15,40,24,0.14), transparent);
  margin:2.4rem 0;
}

.step-num{
  font-family:'Fraunces', serif;
  font-size:1.1rem; font-weight:600;
  color:var(--forest-500);
}

.warn-banner{
  background:var(--warning-bg);
  border:1px solid rgba(199,125,34,0.35);
  border-radius:var(--radius-md);
  padding:1rem 1.2rem;
  color:#7A4E15;
  font-weight:500;
}
.danger-banner{
  background:var(--danger-bg);
  border:1px solid rgba(179,38,30,0.3);
  border-radius:var(--radius-md);
  padding:1rem 1.2rem;
  color:#7A211B;
  font-weight:500;
}

.footer-note{
  text-align:center; color:var(--muted); font-size:0.8rem;
  padding-top:2.4rem;
}

/* fade-in for page content */
.block-container > div:first-child{
  animation: fadeUp 0.5s ease both;
}
@keyframes fadeUp{
  from{opacity:0; transform:translateY(8px);}
  to{opacity:1; transform:translateY(0);}
}

@media (max-width: 640px){
  .block-container{padding-left:1rem; padding-right:1rem;}
  .hero-title{font-size:2rem;}
}
</style>
"""


def inject_theme():
    """Call once near the top of every page to apply the design system."""
    st.markdown(CSS, unsafe_allow_html=True)
