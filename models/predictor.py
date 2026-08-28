"""
The UI never imports disease_model / severity_model directly — it only
calls `run_diagnosis()` below. This means swapping either model, changing
the uncertainty threshold, or adding a third model later never requires
touching any Streamlit page.

Standard result schema (matches the spec exactly):

{
    "crop": "tomato",
    "disease": "Early Blight",
    "disease_confidence": 0.932,
    "severity": "Moderate",
    "severity_confidence": 0.847,
    "uncertain": False,
}
"""

from data.crops import UNCERTAINTY_THRESHOLD
from models import disease_model, severity_model


def run_diagnosis(image, crop: str) -> dict:
    """Run the full disease + severity pipeline on a single leaf image.

    Args:
        image: PIL.Image.Image — the uploaded/captured leaf photo.
        crop: str — crop id selected by the user (e.g. "tomato").

    Returns:
        dict matching the standard result schema described above.
    """
    disease, disease_confidence = disease_model.predict(image, crop)
    uncertain = disease_confidence < UNCERTAINTY_THRESHOLD

    if uncertain:
        # Do not run / trust severity on an already-ambiguous disease call —
        # avoids compounding uncertainty into a fabricated-looking severity.
        return {
            "crop": crop,
            "disease": disease,
            "disease_confidence": disease_confidence,
            "severity": None,
            "severity_confidence": None,
            "uncertain": True,
        }

    severity, severity_confidence = severity_model.predict(image, disease)

    return {
        "crop": crop,
        "disease": disease,
        "disease_confidence": disease_confidence,
        "severity": severity,
        "severity_confidence": severity_confidence,
        "uncertain": False,
    }
