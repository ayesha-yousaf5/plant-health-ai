"""
Real severity classification model using trained EfficientNet-B0.

Downloads the model from cloud storage on first run, then loads the checkpoint
and applies the same transforms used during evaluation.
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
SEVERITY_MODEL_PATH = PROJECT_ROOT / "models" / "weights" / "severity_model.pt"

# Google Drive file ID
SEVERITY_MODEL_ID = "14FShPAXWs7H7IzTBkliX6HrZhDhPsf7o"

# Add project root to path for augmentation module
sys.path.insert(0, str(PROJECT_ROOT))

from augmentation import AutoCropBorders

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Severity label mapping: our format → UI format
SEVERITY_LABEL_MAP = {
    "MILD": "Mild",
    "MODERATE": "Moderate",
    "SEVERE": "Severe",
}

# Global model state
_model = None
_class_to_idx = None
_idx_to_class = None
_transform = None
_device = None


def _download_model_if_needed():
    """Download model from Google Drive if not present locally."""
    if not SEVERITY_MODEL_PATH.exists():
        print(f"Downloading severity model from cloud storage...")
        SEVERITY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://drive.google.com/uc?id={SEVERITY_MODEL_ID}"
        gdown.download(url, str(SEVERITY_MODEL_PATH), quiet=False)
        print(f"Model downloaded to {SEVERITY_MODEL_PATH}")


def _load_model():
    """Load the trained severity model checkpoint."""
    global _model, _class_to_idx, _idx_to_class, _transform, _device

    if _model is not None:
        return

    # Download model if needed
    _download_model_if_needed()

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load checkpoint (weights_only=False needed for numpy arrays in class_to_idx)
    checkpoint = torch.load(SEVERITY_MODEL_PATH, map_location=_device, weights_only=False)
    _class_to_idx = checkpoint["class_to_idx"]
    _idx_to_class = {v: k for k, v in _class_to_idx.items()}

    # Build model architecture (EfficientNet-B0)
    n_classes = len(_class_to_idx)
    _model = models.efficientnet_b0(weights=None)
    # Replace the classifier head
    if hasattr(_model, "classifier"):
        head = _model.classifier
        if isinstance(head, nn.Linear):
            _model.classifier = nn.Linear(head.in_features, n_classes)
        else:
            head[-1] = nn.Linear(head[-1].in_features, n_classes)

    # Load trained weights
    _model.load_state_dict(checkpoint["model_state_dict"])
    _model.to(_device)
    _model.eval()

    # Build eval transform
    _transform = transforms.Compose([
        AutoCropBorders(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    print(f"Severity model loaded: {n_classes} classes, device={_device}")


def predict(image: Image.Image, disease: str) -> tuple[str, float]:
    """Predict severity from a leaf image.

    Args:
        image: PIL Image of the leaf
        disease: disease label (not used by severity model, but kept for API compatibility)

    Returns:
        (severity_label, confidence) where severity is "Mild", "Moderate", or "Severe"
    """
    _load_model()

    # Healthy leaves get Mild severity
    if disease.lower() == "healthy":
        return "Mild", 0.95

    # Apply transforms
    tensor = _transform(image.convert("RGB")).unsqueeze(0).to(_device)

    # Forward pass
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    # Get prediction
    idx = int(probs.argmax())
    severity_raw = _idx_to_class[idx]  # e.g., "MILD", "MODERATE", "SEVERE"
    confidence = float(probs[idx])

    # Map to UI format
    severity = SEVERITY_LABEL_MAP.get(severity_raw, severity_raw)

    return severity, confidence
