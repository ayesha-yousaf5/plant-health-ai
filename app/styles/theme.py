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
    the subject matter instead of a generic progress bar.
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
  --shadow-glow: 0 0 40px rgba(45,106,79,0.15);
}

html, body, [class*="css"]{
  font-family:'Manrope', -apple-system, sans-serif;
  color:var(--ink);
}

.stApp{
  background:
    radial-gradient(ellipse 900px 500px at 8% -10%, rgba(116,165,127,0.14), transparent 60%),
    radial-gradient(ellipse 600px 400px at 92% 90%, rgba(217,164,65,0.06), transparent 60%),
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

a{color:var(--forest-500); transition:color 0.2s ease;}
a:hover{color:var(--forest-700);}

/* ---------- Animations ---------- */
@keyframes fadeUp{
  from{opacity:0; transform:translateY(12px);}
  to{opacity:1; transform:translateY(0);}
}
@keyframes fadeIn{
  from{opacity:0;}
  to{opacity:1;}
}
@keyframes scaleIn{
  from{opacity:0; transform:scale(0.95);}
  to{opacity:1; transform:scale(1);}
}
@keyframes slideInRight{
  from{opacity:0; transform:translateX(20px);}
  to{opacity:1; transform:translateX(0);}
}
@keyframes pulse{
  0%, 100%{transform:scale(1);}
  50%{transform:scale(1.05);}
}
@keyframes shimmer{
  0%{background-position:-200% 0;}
  100%{background-position:200% 0;}
}
@keyframes float{
  0%, 100%{transform:translateY(0);}
  50%{transform:translateY(-6px);}
}

/* Staggered fade-in for page content */
.block-container > div{
  animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.block-container > div:nth-child(1){animation-delay:0.05s;}
.block-container > div:nth-child(2){animation-delay:0.1s;}
.block-container > div:nth-child(3){animation-delay:0.15s;}
.block-container > div:nth-child(4){animation-delay:0.2s;}
.block-container > div:nth-child(5){animation-delay:0.25s;}

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
  transition:all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow:0 2px 4px rgba(15,40,24,0.12);
  position:relative;
  overflow:hidden;
}
.stButton>button::before{
  content:'';
  position:absolute;
  top:50%;
  left:50%;
  width:0;
  height:0;
  border-radius:50%;
  background:rgba(255,255,255,0.15);
  transform:translate(-50%, -50%);
  transition:width 0.6s ease, height 0.6s ease;
}
.stButton>button:hover::before{
  width:300px;
  height:300px;
}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover{
  background:var(--forest-900);
  border-color:var(--forest-900);
  transform:translateY(-2px);
  box-shadow:0 8px 24px -8px rgba(15,40,24,0.45);
  color:#FFFFFF;
}
.stButton>button:active{
  transform:translateY(0);
  box-shadow:0 2px 8px rgba(15,40,24,0.2);
}

/* Secondary / ghost button variant via data attribute set from Python */
button[kind="secondary"]{
  background:transparent !important;
  color:var(--forest-700) !important;
  border:1.5px solid var(--leaf-400) !important;
  transition:all 0.3s ease !important;
}
button[kind="secondary"]:hover{
  background:var(--leaf-200) !important;
  border-color:var(--forest-500) !important;
  color:var(--forest-900) !important;
  transform:translateY(-1px);
}

/* ---------- Inputs ---------- */
.stSelectbox [data-baseweb="select"]>div, .stTextInput input, .stTextArea textarea{
  border-radius:var(--radius-sm) !important;
  border-color:#DDE3DA !important;
  font-family:'Manrope', sans-serif;
  transition:all 0.2s ease !important;
}
.stSelectbox [data-baseweb="select"]>div:focus-within,
.stTextInput input:focus, .stTextArea textarea:focus{
  border-color:var(--forest-500) !important;
  box-shadow:0 0 0 3px rgba(45,106,79,0.1) !important;
}
[data-testid="stFileUploaderDropzone"]{
  background:var(--surface);
  border:2px dashed var(--leaf-400);
  border-radius:var(--radius-md);
  transition:all 0.3s ease;
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:var(--forest-500);
  background:var(--success-bg);
  transform:scale(1.01);
}
[data-testid="stCameraInput"] video{border-radius:var(--radius-md);}

/* ---------- Sidebar / nav ---------- */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg, var(--forest-900) 0%, #0a1f12 100%);
  border-right:none;
  box-shadow:4px 0 24px rgba(0,0,0,0.15);
}
section[data-testid="stSidebar"] *{color:#EFF4F0 !important;}
section[data-testid="stSidebar"] .stButton>button{
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.1);
  width:100%;
  text-align:left;
  border-radius:var(--radius-sm);
  font-weight:600;
  transition:all 0.25s ease;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:rgba(255,255,255,0.1);
  border-color:var(--leaf-400);
  transform:translateX(4px);
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
  transition:all 0.2s ease;
  cursor:default;
}
.pill:hover{
  background:var(--leaf-400);
  color:#fff;
  transform:scale(1.05);
}

.card{
  background:var(--surface);
  border:1px solid rgba(15,40,24,0.06);
  border-radius:var(--radius-lg);
  padding:1.5rem 1.6rem;
  box-shadow:var(--shadow-card);
  transition:all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position:relative;
  overflow:hidden;
}
.card::before{
  content:'';
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:3px;
  background:linear-gradient(90deg, var(--forest-500), var(--leaf-400), var(--gold));
  opacity:0;
  transition:opacity 0.3s ease;
}
.card:hover{
  box-shadow:var(--shadow-card-hover);
  transform:translateY(-4px);
}
.card:hover::before{
  opacity:1;
}
.card.tight{padding:1.1rem 1.2rem;}

.crop-card{
  background:var(--surface);
  border:1.5px solid rgba(15,40,24,0.07);
  border-radius:var(--radius-md);
  padding:1.1rem 1rem;
  text-align:center;
  transition:all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  cursor:pointer;
  position:relative;
  overflow:hidden;
}
.crop-card::after{
  content:'';
  position:absolute;
  inset:0;
  border-radius:inherit;
  background:radial-gradient(circle at center, rgba(45,106,79,0.08) 0%, transparent 70%);
  opacity:0;
  transition:opacity 0.3s ease;
}
.crop-card:hover{
  border-color:var(--leaf-400);
  transform:translateY(-4px) scale(1.02);
  box-shadow:var(--shadow-card-hover);
}
.crop-card:hover::after{
  opacity:1;
}
.crop-card:hover .crop-emoji{
  animation:float 1.5s ease-in-out infinite;
}
.crop-card.selected{
  border-color:var(--forest-700);
  background:var(--success-bg);
  box-shadow:0 0 0 3px rgba(45,106,79,0.12), var(--shadow-card);
}
.crop-emoji{font-size:1.9rem; line-height:1; transition:transform 0.3s ease;}
.crop-name{font-weight:700; font-size:0.92rem; margin-top:0.35rem; color:var(--forest-900);}
.crop-blurb{font-size:0.74rem; color:var(--muted); margin-top:0.15rem;}

.badge{
  display:inline-flex; align-items:center; gap:0.35rem;
  font-weight:700; font-size:0.82rem;
  padding:0.32rem 0.75rem; border-radius:999px;
  animation:scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
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
  animation:fadeIn 0.6s ease;
}

.hero-wrap{
  padding:3.2rem 0 1.6rem 0;
  animation:fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
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
  animation:fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
}
.hero-accent{
  color:var(--forest-500);
  font-style:italic;
  background:linear-gradient(120deg, var(--forest-500), var(--leaf-400));
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
}

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
  animation:scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.danger-banner{
  background:var(--danger-bg);
  border:1px solid rgba(179,38,30,0.3);
  border-radius:var(--radius-md);
  padding:1rem 1.2rem;
  color:#7A211B;
  font-weight:500;
  animation:scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.footer-note{
  text-align:center; color:var(--muted); font-size:0.8rem;
  padding-top:2.4rem;
}

/* Spinner animation */
.stSpinner > div{
  animation:pulse 1.5s ease-in-out infinite;
}

/* Expander animation */
.streamlit-expanderHeader{
  transition:all 0.2s ease !important;
}
.streamlit-expanderHeader:hover{
  background:var(--surface-alt) !important;
}

/* Tabs animation */
.stTabs [data-baseweb="tab-list"]{
  gap:0.5rem;
}
.stTabs [data-baseweb="tab"]{
  border-radius:var(--radius-sm) var(--radius-sm) 0 0 !important;
  transition:all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover{
  background:var(--surface-alt) !important;
}
.stTabs [aria-selected="true"]{
  border-bottom:2px solid var(--forest-500) !important;
}

/* Chat messages animation */
[data-testid="stChatMessage"]{
  animation:slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Info/Success/Error boxes animation */
.stAlert{
  animation:scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  border-radius:var(--radius-md) !important;
}

@media (max-width: 640px){
  .block-container{padding-left:1rem; padding-right:1rem;}
  .hero-title{font-size:2rem;}
}

/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{
    animation-duration:0.01ms !important;
    animation-iteration-count:1 !important;
    transition-duration:0.01ms !important;
  }
}
</style>
"""


def inject_theme():
    """Call once near the top of every page to apply the design system."""
    st.markdown(CSS, unsafe_allow_html=True)
