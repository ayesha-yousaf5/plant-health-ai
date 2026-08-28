"""
Severity assessment model interface.

===========================================================================
 INTEGRATION POINT #2 — REAL SEVERITY MODEL GOES HERE
===========================================================================
Replace the body of `predict(image, disease)` with a call into the trained
severity-regression/classification model. Keep the signature and return
type IDENTICAL:

    def predict(image: PIL.Image.Image, disease: str) -> tuple[str, float]:
        return severity_label, confidence   # severity in {"Mild","Moderate","Severe"}

If the real model outputs a continuous infected-area percentage, bucket it
into the three labels HERE (server-side) so the UI never receives or shows
a raw percentage — that's a product requirement, not just a UI choice:

    def _bucket(pct: float) -> str:
        if pct < 15: return "Mild"
        if pct < 45: return "Moderate"
        return "Severe"

    def predict(image, disease):
        pct, confidence = _severity_regressor(image)
        return _bucket(pct), confidence
===========================================================================
"""

import hashlib
import random

from data.crops import SEVERITY_LEVELS


def predict(image, disease: str) -> tuple[str, float]:
    """Mock severity prediction, deterministic per (image, disease)."""
    if disease.lower() == "healthy":
        return "Mild", round(random.Random(1).uniform(0.9, 0.99), 3)

    seed = _seed_from_image(image, disease)
    rng = random.Random(seed)

    severity = rng.choices(SEVERITY_LEVELS, weights=[0.35, 0.4, 0.25])[0]
    confidence = round(rng.uniform(0.68, 0.96), 3)
    return severity, confidence


def _seed_from_image(image, disease: str) -> int:
    try:
        thumb = image.copy()
        thumb.thumbnail((16, 16))
        digest = hashlib.md5(thumb.tobytes() + disease.encode() + b"sev").hexdigest()
        return int(digest[:8], 16)
    except Exception:
        return random.randint(0, 1_000_000)
