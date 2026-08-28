# 🌿 Plant Health AI — Disease Detection & Severity Assessment

A Streamlit web interface for the Plant Disease Detection & Severity
Assessment system, built against the **PlantInquiryVQA** dataset.

This repo covers the **Web Interface + UI Integration + Deployment** slice
of the project: a complete, working, end-to-end demo flow running on mock
predictions, with clearly marked seams where the real disease model,
severity model, and Qwen assistant get plugged in.

```
Home → Start Diagnosis → Select Crop → Upload/Capture Leaf →
Analyze → Disease Prediction → Confidence → Severity →
Uncertainty Handling → AI Assistant
```

---

## 1. Project structure

```
plant-health-ai/
│
├── app/
│   ├── app.py                     # Home page (Streamlit entry point)
│   ├── pages/
│   │   ├── 1_🔬_Diagnosis.py       # Crop select + upload/capture + analyze
│   │   ├── 2_📊_Results.py         # Prediction, confidence, severity, uncertainty
│   │   ├── 3_🤖_Assistant.py       # Chat UI grounded in the diagnosis
│   │   └── 4_ℹ️_About.py           # Overview, dataset, methodology, limitations
│   ├── components/
│   │   ├── state.py               # st.session_state schema (single source of truth)
│   │   ├── nav.py                 # Sidebar navigation + live diagnosis context
│   │   └── ui.py                  # Cards, badges, hero, signature "leaf gauge" SVG
│   └── styles/
│       └── theme.py               # Design tokens + global CSS (fonts, colors, components)
│
├── models/
│   ├── disease_model.py           # 🔌 INTEGRATION POINT #1 — real disease classifier
│   ├── severity_model.py          # 🔌 INTEGRATION POINT #2 — real severity model
│   └── predictor.py               # Orchestrates both into the standard result schema
│
├── chatbot/
│   └── qwen_assistant.py          # 🔌 INTEGRATION POINT #3 — real Qwen API call
│
├── data/
│   └── crops.py                   # Supported crops, mock disease vocab, thresholds
│
├── results/                       # Scratch space for exported reports (empty for now)
│
├── .streamlit/
│   └── config.toml                # Base Streamlit theme
│
├── requirements.txt
└── README.md
```

---

## 2. Installation

```bash
# from inside plant-health-ai/
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## 3. Running the app

```bash
streamlit run app/app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) and,
importantly for hackathon demo purposes, a **Network URL** you can open on
a phone connected to the same Wi-Fi — the multipage navigation, camera
capture, and layout are all responsive down to mobile widths.

---

## 4. How the mock prediction works

The UI never calls a model file directly — every page goes through a
single function:

```python
from models.predictor import run_diagnosis

result = run_diagnosis(image, crop)
```

which returns the standard result schema:

```json
{
  "crop": "tomato",
  "disease": "early_blight",
  "disease_confidence": 0.932,
  "severity": "moderate",
  "severity_confidence": 0.847,
  "uncertain": false
}
```

Internally, `run_diagnosis()`:

1. Calls `models/disease_model.predict(image, crop)` → `(disease, confidence)`.
2. If `disease_confidence` is below `UNCERTAINTY_THRESHOLD` (0.60, set in
   `data/crops.py`), it stops there and returns `uncertain: true` with
   `severity` fields set to `None` — the Results page then shows the
   "image is ambiguous, please re-upload" flow instead of a diagnosis.
3. Otherwise it calls `models/severity_model.predict(image, disease)` →
   `(severity, confidence)` and returns the full result.

The mock disease/severity functions are **deterministic per image** (hashed
from a downsized thumbnail) so re-analyzing the same photo gives a stable
demo result, while different photos/crops produce different outcomes —
including an occasional low-confidence case, so the uncertainty-handling
path is easy to show live.

---

## 5. Where the real models plug in

Each integration point is documented in-place with a docstring showing the
expected real implementation. In short:

### 🔌 Disease model → `models/disease_model.py`

```python
def predict(image: PIL.Image.Image, crop: str) -> tuple[str, float]:
    ...
    return disease_label, confidence   # confidence in [0.0, 1.0]
```

Swap the mock body for the trained PlantInquiryVQA classifier. Keep the
signature and return type identical — nothing else in the app needs to
change.

### 🔌 Severity model → `models/severity_model.py`

```python
def predict(image: PIL.Image.Image, disease: str) -> tuple[str, float]:
    ...
    return severity_label, confidence   # severity in {"Mild","Moderate","Severe"}
```

If the trained model outputs a continuous infected-area percentage,
**bucket it into the three tiers inside this file** — the UI is intentionally
built to never receive or display a raw percentage.

### 🔌 Qwen assistant → `chatbot/qwen_assistant.py`

```python
def ask(message: str, context: dict, history: list) -> str:
    ...
    return reply_text
```

`context` carries the current diagnosis (`crop`, `disease`, `severity`,
`disease_confidence`, `severity_confidence`) so the real prompt can stay
grounded in the actual result instead of giving generic advice. Keep the
"general management guidance, not an exact prescription" framing in the
system prompt when you connect the real model — it's a product requirement,
not just mock-response flavor text.

---

## 6. Design notes

- **Palette**: forest green (`#1B4332` / `#2D6A4F`) on a warm paper
  background (`#F7F6F1`), with a harvest-gold accent (`#D9A441`) for
  confidence highlights — chosen specifically to avoid the generic
  "AI-product terracotta" look.
- **Type**: Fraunces (serif, headlines) + Manrope (body) + IBM Plex Mono
  (confidence numbers / data readouts).
- **Signature element**: the "leaf gauge" — a leaf-shaped SVG that fills
  bottom-to-top to represent a confidence percentage, used throughout the
  Results page instead of a generic progress bar.

---

## 7. What's intentionally out of scope (per hackathon constraints)

No native mobile app, no YOLO object detection, no weather/GPS/IoT
integration, no yield prediction, no voice assistant, no user accounts, no
custom LLM training, and no exact pesticide dosage system. The goal of this
slice is a reliable, demoable, integration-ready web interface.
