"""Shared configuration for the 10-crop class-imbalance augmentation pipeline.

Every decision that affects the dataset lives here so all pipeline stages agree.
Override DATA_ROOT via the PLANTDIS_ROOT env var to run on Kaggle unchanged.
"""

import os
from pathlib import Path

DATA_ROOT = Path(os.environ.get("PLANTDIS_ROOT", r"D:\plantdis"))


def _load_dotenv(path: Path = DATA_ROOT / ".env") -> None:
    """Read KEY=VALUE lines from the gitignored .env into the environment.

    Kept dependency-free. Existing environment variables win, so an explicitly
    exported value is never silently overridden by the file.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

RAW_TRAIN_QA = DATA_ROOT / "plantinquiryvqa_train.csv"
RAW_TEST_QA = DATA_ROOT / "data" / "raw" / "test.csv"
IMAGES_DIR = DATA_ROOT / "data" / "raw" / "hf" / "images"

PROCESSED = DATA_ROOT / "data" / "processed"
AUGMENTED_DIR = PROCESSED / "augmented"
REPORTS = DATA_ROOT / "reports"
CONTACT_SHEETS = REPORTS / "contact_sheets"

MASTER_METADATA = PROCESSED / "master_metadata.csv"
CLASS_DECISIONS = PROCESSED / "class_decisions.csv"
SPLITS = PROCESSED / "splits.csv"
AUG_MANIFEST = PROCESSED / "train_augmented_manifest.csv"
AUG_CONFIG = PROCESSED / "augmentation_config.json"

# --- crop scope -------------------------------------------------------------
# Cucumber and Eggplant/Brinjal are owned by other team members.
# Cotton was originally another member's assignment but was added on request:
# coordinate before delivery so two people do not ship different Cotton data.
CROPS = [
    "Corn",
    "Rice",
    "Apple",
    "Potato",
    "Tomato",
    "Mango",
    "Grape",
    "Peas",
    "Sunflower",
    "Pepper Chilli",
    "Cotton",
]

# 'Pepper' carries 6 disease classes but no healthy images; 'Pepper Bell' carries
# the healthy set. Both are Capsicum annuum, so they form one user-facing crop.
CROP_MERGE = {"Pepper": "Pepper Chilli", "Pepper Bell": "Pepper Chilli"}

# --- class removals agreed in PlantInquiryVQA_12_Crop_Selection.csv ----------
TEAM_DROP_CLASSES = {
    "Tomato": ["Mosaic Virus", "Yellowing Symptom", "Fusarium Wilt"],
    "Grape": ["Anthracnose", "Powdery Mildew"],
    "Peas": ["Stem Rot", "Downy Mildew", "Leaf Roll Virus", "Anthracnose", "Powdery Mildew"],
    "Sunflower": ["Downy Mildew", "Powdery Mildew"],
    "Mango": ["senescence", "senescence or dry"],
}

# --- duplicate-label normalisation ------------------------------------------
# Confirmed by contact-sheet review (reports/contact_sheets/). Each pair is one
# disease recorded twice under different names, from two different source
# datasets. Merging is normalisation, which the guidelines require; merging
# distinct biology to inflate counts is forbidden and is not what these are.
#
# Merging also mitigates a measured confound: keeping a disease split across two
# photo sources is exactly what lets a model learn source instead of pathology.
#
#   Apple scab pair          - high confidence: same studio backgrounds, same
#                              olive-brown lesions, differ only in resolution
#   Tomato spider mites pair - high confidence: same chlorotic stippling
#   Tomato leaf mold pair    - moderate: both yellow chlorotic blotching, but A
#                              shows discrete spots and B more diffuse yellowing
#   Corn gray leaf spot pair - Cercospora zeae-maydis IS gray leaf spot, so the
#                              names are true synonyms; note the target class
#                              mixes studio and field photos and is noisier
LABEL_MERGE_PAIRS = [
    ("Corn", "Cercospora Leaf Spot Gray Leaf Spot", "Gray Leaf Spot"),
    ("Apple", "Apple Apple Scab", "Apple Scab"),
    ("Tomato", "Spider Mites Spider Mites", "Spider Mites"),
    ("Tomato", "Cercospora Leaf Mold", "Leaf Mold"),
]
APPLY_LABEL_MERGES = True

# Only 40.3% of metadata rows have an actual image file, so a pixel-backed floor
# of 40 would have been far stricter than the team's agreed standard (their floor
# of 39 on HF-train metadata converts to roughly 26 pixel-backed images).
MIN_CLASS_SIZE = 20

# --- split ------------------------------------------------------------------
# HF ships a 60/40 train/test split (verified image-disjoint, zero overlap).
# We merge both and re-split to recover ~48% more training data.
SPLIT_RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}
SPLIT_SEED = 42

# A single 10% holdout leaves a 20-image class with only ~2 val images, where one
# error moves recall by 50 points. splits.csv therefore also carries a fold column
# over the train+val rows so the same file supports both protocols: the frozen
# holdout for the three-backbone comparison, and k-fold CV for headline per-class
# numbers. Caveat to report: stratification shrinks apparent fold-to-fold spread
# for rare classes, so fold std is an optimistic uncertainty estimate.
N_FOLDS = 5

# --- augmentation -----------------------------------------------------------
# Balance by SAMPLING with fresh random transforms each epoch, not by writing a
# fixed number of augmented copies per source image. Buda et al. (2018) found
# oversampling to full balance does not overfit CNNs, but materialising N copies
# caps a class at N variants the model can memorise, whereas online transforms
# draw from a continuous distribution. Our binding limit is real images (as few
# as 20 per class); no augmentation ratio raises that information ceiling.
AUGMENTATION_MODE = "online"

# No hue or saturation shifts: disease identity here is partly defined by colour
# (Yellow Leaf Spot, Sooty Mould, Tungro yellowing), so recolouring the leaf
# would change the ground-truth label. Brightness/contrast is capped to simulate
# lighting only. No elastic distortion and no cutout, which can erase the lesion
# that carries the label.
AUG_PARAMS = {
    "horizontal_flip_p": 0.5,
    "vertical_flip_p": 0.5,
    "rotation_deg": 15,
    "zoom_range": [0.85, 1.0],
    "brightness_range": [0.8, 1.2],
    "contrast_range": [0.8, 1.2],
    "output_size": 224,
    "jpeg_quality": 95,
    "excluded": ["hue_shift", "saturation_shift", "elastic_distortion", "cutout", "random_erasing"],
}
AUG_SEED = 1337

# Rebalancing method. Oversampling and class-weighted loss both correct the same
# skew, so applying both at full strength over-corrects minority classes and
# hurts precision and calibration. Pick one.
REBALANCE = "sampler"  # "sampler" | "class_weights" | "none"

# A severity band needs at least this many real images before we will synthesise
# up to the target. Below it, padding 20x+ from a handful of leaves teaches the
# model those specific leaves, so the band is reported as a stated limitation.
MIN_REAL_FOR_BAND_AUG = 40

SEVERITY_BANDS = ["MILD", "MODERATE", "SEVERE"]
# Healthy and other non-disease rows carry no severity. The guidelines call this
# "N/A", but that literal is in pandas' default na_values list, so it round-trips
# through CSV as NaN and breaks equality checks. "NONE" means the same thing and
# survives being written and read back.
NO_SEVERITY = "NONE"
