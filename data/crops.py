"""
Reference data for the Plant Disease Detection & Severity Assessment system.

This module intentionally holds no model logic. It only describes what the
UI is allowed to offer (supported crops) and what labels the mock predictor
draws from until the real PlantInquiryVQA-trained model is wired in.

When the real model is connected, DISEASE_CLASSES per crop should be
replaced with the model's actual output class list so the UI vocabulary
never has to change.
"""

# Crops selectable in the Diagnosis flow.
# Updated to match our trained model's crop coverage.
SUPPORTED_CROPS = [
    {"id": "maize", "label": "Corn / Maize", "emoji": "🌽",
     "blurb": "Rust, leaf spot, blight"},
    {"id": "rice", "label": "Rice", "emoji": "🌾",
     "blurb": "Blast, bacterial blight"},
    {"id": "cotton", "label": "Cotton", "emoji": "🧶",
     "blurb": "Bacterial blight, leaf curl virus"},
    {"id": "apple", "label": "Apple", "emoji": "🍏",
     "blurb": "Scab, black rot, rust"},
    {"id": "potato", "label": "Potato", "emoji": "🥔",
     "blurb": "Early & late blight"},
    {"id": "tomato", "label": "Tomato", "emoji": "🍅",
     "blurb": "Blight, mosaic virus, leaf mold"},
    {"id": "mango", "label": "Mango", "emoji": "🥭",
     "blurb": "Anthracnose, powdery mildew"},
    {"id": "grape", "label": "Grape", "emoji": "🍇",
     "blurb": "Black rot, esca, leaf blight"},
    {"id": "peas", "label": "Peas", "emoji": "🫛",
     "blurb": "Powdery mildew, rust"},
    {"id": "sunflower", "label": "Sunflower", "emoji": "🌻",
     "blurb": "Downy mildew, rust, leaf spot"},
    {"id": "pepper", "label": "Pepper / Chilli", "emoji": "🌶️",
     "blurb": "Thrips, blight, mites"},
]

CROP_IDS = [c["id"] for c in SUPPORTED_CROPS]

# Disease vocabulary per crop — placeholder for UI reference.
# The real model handles class names internally via class_to_idx.
DISEASE_CLASSES = {
    "maize": ["Common Rust", "Gray Leaf Spot", "Northern Leaf Blight", "Healthy"],
    "rice": ["Bacterial Leaf Blight", "Rice Blast", "Brown Spot", "Healthy"],
    "cotton": ["Bacterial Blight", "Leaf Curl Virus", "Boll Rot", "Healthy"],
    "apple": ["Apple Scab", "Black Rot", "Cedar Apple Rust", "Healthy"],
    "potato": ["Early Blight", "Late Blight", "Healthy"],
    "tomato": ["Early Blight", "Late Blight", "Leaf Mold", "Mosaic Virus", "Septoria Leaf Spot", "Healthy"],
    "mango": ["Anthracnose", "Powdery Mildew", "Bacterial Canker", "Healthy"],
    "grape": ["Black Rot", "Esca (Black Measles)", "Leaf Blight", "Healthy"],
    "peas": ["Powdery Mildew", "Rust", "Bacterial Blight", "Healthy"],
    "sunflower": ["Downy Mildew", "Rust", "Leaf Spot", "Healthy"],
    "pepper": ["Thrips", "Blight", "Mites", "Spot", "Healthy"],
}

SEVERITY_LEVELS = ["Mild", "Moderate", "Severe"]

# Confidence threshold below which a prediction is treated as "uncertain"
# and the UI must refuse to present it as a definite diagnosis.
UNCERTAINTY_THRESHOLD = 0.60
