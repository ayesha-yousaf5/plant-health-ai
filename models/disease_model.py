"""
Disease classification model interface.

===========================================================================
 INTEGRATION POINT #1 — REAL DISEASE MODEL GOES HERE
===========================================================================
Replace the body of `predict(image, crop)` with a call into the trained
PlantInquiryVQA-based classifier. Keep the function signature and return
type IDENTICAL so nothing else in the app needs to change:

    def predict(image: PIL.Image.Image, crop: str) -> tuple[str, float]:
        return disease_label, confidence   # confidence in [0.0, 1.0]

Typical real implementation:

    from torchvision import transforms
    _model = torch.load("models/weights/disease_classifier.pt")
    _model.eval()

    def predict(image, crop):
        tensor = _TRANSFORM(image.convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            logits = _model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
        idx = int(probs.argmax())
        return CLASS_NAMES[crop][idx], float(probs[idx])
===========================================================================
"""

import hashlib
import random

from data.crops import DISEASE_CLASSES


def predict(image, crop: str) -> tuple[str, float]:
    """Mock disease prediction.

    Deterministic per (image bytes, crop) so re-running "Analyze" on the
    same image gives a stable demo result, while different images/crops
    vary — this makes the hackathon demo look intentional rather than
    random every click.
    """
    classes = DISEASE_CLASSES.get(crop, ["Unknown"])
    seed = _seed_from_image(image, crop)
    rng = random.Random(seed)

    disease = rng.choice(classes)
    # Bias confidence to mostly-confident with an occasional ambiguous case,
    # so the uncertainty-handling UI path is easy to demo.
    if rng.random() < 0.18:
        confidence = round(rng.uniform(0.32, 0.58), 3)
    else:
        confidence = round(rng.uniform(0.72, 0.98), 3)

    return disease, confidence


def _seed_from_image(image, crop: str) -> int:
    try:
        thumb = image.copy()
        thumb.thumbnail((16, 16))
        digest = hashlib.md5(thumb.tobytes() + crop.encode()).hexdigest()
        return int(digest[:8], 16)
    except Exception:
        return random.randint(0, 1_000_000)
