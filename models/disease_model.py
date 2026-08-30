"""
Real disease classification model using trained ResNet50.

Downloads the model from cloud storage on first run, then loads the checkpoint
and applies the same transforms used during evaluation (AutoCropBorders + ImageNet normalization).
"""

import sys
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
import gdown

# Model paths - relative to repo root
PROJECT_ROOT = Path(__file__).parent.parent
DISEASE_MODEL_PATH = PROJECT_ROOT / "models" / "weights" / "disease_model.pt"

# Google Drive file ID
DISEASE_MODEL_ID = "1OGIp67N5JGP890su0KYXjSKTV4kZ8MYI"

# Add project root to path for augmentation module
sys.path.insert(0, str(PROJECT_ROOT))

from augmentation import AutoCropBorders

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Crop name mapping: UI format → our format
CROP_NAME_MAP = {
    "maize": "Corn",
    "rice": "Rice",
    "cotton": "Cotton",
    "apple": "Apple",
    "potato": "Potato",
    "tomato": "Tomato",
    "mango": "Mango",
    "grape": "Grape",
    "peas": "Peas",
    "sunflower": "Sunflower",
    "pepper": "Pepper Chilli",
}

# Global model state
_model = None
_class_to_idx = None
_idx_to_class = None
_transform = None
_device = None


def _download_model_if_needed():
    """Download model from Google Drive if not present locally."""
    if not DISEASE_MODEL_PATH.exists():
        print(f"Downloading disease model from cloud storage...")
        DISEASE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://drive.google.com/uc?id={DISEASE_MODEL_ID}"
        gdown.download(url, str(DISEASE_MODEL_PATH), quiet=False)
        print(f"Model downloaded to {DISEASE_MODEL_PATH}")


def _load_model():
    """Load the trained model checkpoint."""
    global _model, _class_to_idx, _idx_to_class, _transform, _device

    if _model is not None:
        return

    # Download model if needed
    _download_model_if_needed()

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load checkpoint (weights_only=False needed for numpy arrays in class_to_idx)
    checkpoint = torch.load(DISEASE_MODEL_PATH, map_location=_device, weights_only=False)
    _class_to_idx = checkpoint["class_to_idx"]
    _idx_to_class = {v: k for k, v in _class_to_idx.items()}

    # Build model architecture (ResNet50)
    n_classes = len(_class_to_idx)
    _model = models.resnet50(weights=None)
    # Replace the classifier head
    if hasattr(_model, "classifier"):
        head = _model.classifier
        if isinstance(head, nn.Linear):
            _model.classifier = nn.Linear(head.in_features, n_classes)
        else:
            head[-1] = nn.Linear(head[-1].in_features, n_classes)
    elif hasattr(_model, "fc"):
        _model.fc = nn.Linear(_model.fc.in_features, n_classes)

    # Load trained weights
    _model.load_state_dict(checkpoint["model_state_dict"])
    _model.to(_device)
    _model.eval()

    # Build eval transform (same as training)
    _transform = transforms.Compose([
        AutoCropBorders(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    print(f"Disease model loaded: {n_classes} classes, device={_device}")


def predict(image: Image.Image, crop: str) -> tuple[str, float]:
    """Predict disease from a leaf image.

    Args:
        image: PIL Image of the leaf
        crop: crop id from UI (e.g., "tomato", "maize")

    Returns:
        (disease_label, confidence) where confidence is in [0, 1]
    """
    _load_model()

    # Apply transforms
    tensor = _transform(image.convert("RGB")).unsqueeze(0).to(_device)

    # Forward pass
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    # Get prediction
    idx = int(probs.argmax())
    full_label = _idx_to_class[idx]  # e.g., "Tomato|Early Blight"
    confidence = float(probs[idx])

    # Extract disease name (after the |)
    if "|" in full_label:
        disease = full_label.split("|")[1]
    else:
        disease = full_label

    return disease, confidence
