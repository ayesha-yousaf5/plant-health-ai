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
# `emoji` and `blurb` are purely presentational (used on the crop selector cards).
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
    {"id": "cucumber", "label": "Cucumber", "emoji": "🥒",
     "blurb": "Downy & powdery mildew"},
    {"id": "eggplant", "label": "Eggplant / Brinjal", "emoji": "🍆",
     "blurb": "Bacterial wilt, leaf spot"},
    {"id": "grape", "label": "Grape", "emoji": "🍇",
     "blurb": "Black rot, esca, leaf blight"},
    {"id": "peas", "label": "Peas", "emoji": "🫛",
     "blurb": "Powdery mildew, rust"},
    {"id": "sunflower", "label": "Sunflower", "emoji": "🌻",
     "blurb": "Downy mildew, rust, leaf spot"},
]

CROP_IDS = [c["id"] for c in SUPPORTED_CROPS]

# Placeholder disease vocabulary per crop, used only by the mock predictor.
# Replace with the trained model's real class list at integration time.
DISEASE_CLASSES = {
    "maize": ["Common Rust", "Gray Leaf Spot", "Northern Leaf Blight", "Healthy"],
    "rice": ["Bacterial Leaf Blight", "Rice Blast", "Brown Spot", "Healthy"],
    "cotton": ["Bacterial Blight", "Leaf Curl Virus", "Boll Rot", "Healthy"],
    "apple": ["Apple Scab", "Black Rot", "Cedar Apple Rust", "Healthy"],
    "potato": ["Early Blight", "Late Blight", "Healthy"],
    "tomato": ["Early Blight", "Late Blight", "Leaf Mold", "Mosaic Virus", "Septoria Leaf Spot", "Healthy"],
    "mango": ["Anthracnose", "Powdery Mildew", "Bacterial Canker", "Healthy"],
    "cucumber": ["Downy Mildew", "Powdery Mildew", "Angular Leaf Spot", "Healthy"],
    "eggplant": ["Bacterial Wilt", "Leaf Spot", "Little Leaf Disease", "Healthy"],
    "grape": ["Black Rot", "Esca (Black Measles)", "Leaf Blight", "Healthy"],
    "peas": ["Powdery Mildew", "Rust", "Bacterial Blight", "Healthy"],
    "sunflower": ["Downy Mildew", "Rust", "Leaf Spot", "Healthy"],
}

SEVERITY_LEVELS = ["Mild", "Moderate", "Severe"]

# Confidence threshold below which a prediction is treated as "uncertain"
# and the UI must refuse to present it as a definite diagnosis.
UNCERTAINTY_THRESHOLD = 0.60
