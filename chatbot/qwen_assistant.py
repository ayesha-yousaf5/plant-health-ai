"""
Conversational assistant interface.

===========================================================================
 INTEGRATION POINT #3 — REAL QWEN API GOES HERE
===========================================================================
Replace the body of `ask(message, context, history)` with a real call to
the hosted Qwen endpoint. Keep the signature and return type IDENTICAL
(a plain string reply) so the chat page needs no changes:

    import requests

    def ask(message, context, history):
        payload = {
            "model": "qwen2.5-plant-advisor",
            "messages": _build_messages(message, context, history),
            "temperature": 0.4,
        }
        resp = requests.post(QWEN_ENDPOINT, json=payload, headers=AUTH_HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

`context` is a dict with keys: crop, disease, severity, disease_confidence,
severity_confidence — i.e. the same diagnosis result the Results page shows.
Feed it into the system prompt so answers stay grounded in the actual
diagnosis instead of generic advice.

IMPORTANT PRODUCT CONSTRAINT (keep in the real system prompt too):
The assistant gives general "Management Guidance", not exact pesticide
dosage or a medical-style prescription. Mock responses below follow that
rule on purpose — do not remove the disclaimer language when connecting
the real model.
===========================================================================
"""

import random

_DISCLAIMER = (
    "This is general management guidance, not an exact treatment prescription. "
    "Confirm product choice and dosage with a local agricultural extension "
    "officer or the product label before applying anything."
)

_GUIDANCE_TEMPLATES = {
    "mild": [
        "At a mild stage, focus on prevention and monitoring:\n"
        "- Remove and dispose of the affected leaves away from the field.\n"
        "- Improve airflow around plants (spacing, pruning lower leaves).\n"
        "- Avoid overhead watering; water at the base in the morning.\n"
        "- Re-check the plant in 3–4 days for spread.",
    ],
    "moderate": [
        "At a moderate stage, act a bit more decisively:\n"
        "- Isolate or prioritize the affected plants for closer monitoring.\n"
        "- Remove heavily affected leaves and any fallen debris nearby.\n"
        "- Consider a locally-recommended fungicide/bactericide suited to this "
        "disease — check with a nearby agri-input store for the right product.\n"
        "- Reduce leaf wetness duration (spacing, drainage, watering time).",
    ],
    "severe": [
        "At a severe stage, the priority is stopping spread to nearby plants:\n"
        "- Remove and destroy badly infected plants/leaves promptly (do not compost).\n"
        "- Disinfect tools between plants to avoid spreading it further.\n"
        "- Consult a local agricultural extension officer for a stage-appropriate "
        "treatment plan — severe cases often need a targeted product and timing.\n"
        "- Monitor neighboring plants closely for early symptoms.",
    ],
}

_GENERIC_FALLBACK = (
    "I can share general management guidance for the diagnosed condition, "
    "explain what the severity level typically means, or suggest what to "
    "monitor next. What would help most right now?"
)


def ask(message: str, context: dict, history: list) -> str:
    """Mock assistant reply, grounded in the current diagnosis context.

    Args:
        message: the user's latest chat message.
        context: dict with crop, disease, severity, disease_confidence,
                 severity_confidence (may have severity=None if uncertain).
        history: list of prior {"role": ..., "content": ...} turns (unused
                 by the mock, but threaded through so the real integration
                 can build multi-turn context immediately).

    Returns:
        A plain-text reply string.
    """
    msg = (message or "").lower().strip()
    crop = context.get("crop", "your crop")
    disease = context.get("disease", "the detected condition")
    severity = (context.get("severity") or "moderate").lower()

    if not context.get("disease") or context.get("uncertain"):
        return (
            "I don't have a confirmed diagnosis to work from yet — the last "
            "image was flagged as ambiguous. Please run a new diagnosis with "
            "a clearer, well-lit photo of the affected leaf, and I'll be able "
            "to give guidance specific to it."
        )

    if any(k in msg for k in ["what should i do", "treatment", "guidance", "help", "recommend", "advice"]):
        body = random.choice(_GUIDANCE_TEMPLATES.get(severity, _GUIDANCE_TEMPLATES["moderate"]))
        return f"For **{disease}** on **{crop}** ({severity} severity):\n\n{body}\n\n_{_DISCLAIMER}_"

    if any(k in msg for k in ["confidence", "sure", "accurate", "certain"]):
        dconf = context.get("disease_confidence")
        sconf = context.get("severity_confidence")
        return (
            f"The disease prediction was made with "
            f"{dconf * 100:.0f}% confidence, and the severity assessment with "
            f"{sconf * 100:.0f}% confidence. If either feels off compared to what "
            f"you're seeing on the plant, re-run the diagnosis with a sharper, "
            f"well-lit close-up of the affected area."
        )

    if any(k in msg for k in ["spread", "contagious", "other plant", "neighbor"]):
        return (
            f"{disease} can spread to nearby plants of the same or related crops, "
            f"especially in humid conditions. Isolating or closely monitoring "
            f"neighboring {crop} plants is a reasonable precaution while you "
            f"manage this one. {_DISCLAIMER}"
        )

    if any(k in msg for k in ["what is", "explain", "mean"]):
        return (
            f"**{disease}** is the condition detected on your {crop} leaf, at a "
            f"**{severity}** severity level based on visible symptoms in the image. "
            f"Ask me for management guidance if you'd like next steps."
        )

    return _GENERIC_FALLBACK
