"""Online augmentation, dataset and balanced sampler for the disease/severity tasks.

Import this from training code so all three backbone experiments share identical
preprocessing. Augmentation is generated fresh each epoch rather than written to
disk: a fixed set of N materialised copies caps a class at N variants the model
can memorise, while online transforms draw from a continuous distribution. This
also keeps the k-fold protocol safe, since there are no pre-baked augmented files
that could follow their parent image into a validation fold.

Augmentation applies to training data ONLY. Eval transforms are deterministic.
"""

import sys
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset, WeightedRandomSampler
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Source images are letterboxed into a uniform 1024x1024 canvas with black
# padding: ~25% carry a 256x256 original (content = 6% of area), ~50% a 1024x768
# original, ~25% are full frame. The padding geometry is close to a class label
# (61 of 84 classes are >95% a single padding pattern, because classes come from
# different source datasets), so a model could score well by reading the border
# instead of the leaf. Cropping to content removes that shortcut.
BLACK_THRESHOLD = 12


class AutoCropBorders:
    """Crop to the non-black content bounding box.

    Preprocessing, not augmentation: it must run for val and test too, otherwise
    evaluation images keep the padding signature that training no longer sees.
    """

    def __init__(self, threshold: int = BLACK_THRESHOLD, min_frac: float = 0.01):
        self.threshold = threshold
        self.min_frac = min_frac

    def __call__(self, img: Image.Image) -> Image.Image:
        grey = img.convert("L")
        bbox = grey.point(lambda v: 255 if v > self.threshold else 0).getbbox()
        if bbox is None:
            return img
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # Guard against a near-black image collapsing to a few stray pixels.
        if w * h < self.min_frac * img.width * img.height:
            return img
        return img.crop(bbox)


def build_train_transform() -> transforms.Compose:
    """Random transforms, resampled on every __getitem__ call.

    Deliberately excludes hue and saturation jitter. Disease identity here is
    partly defined by colour (Yellow Leaf Spot, Sooty Mould, Tungro yellowing),
    so shifting hue would change the ground truth. Brightness and contrast stay
    within +/-20% to simulate lighting rather than recolour the leaf. Also
    excludes cutout/erasing, which can delete the lesion that carries the label.
    """
    p = C.AUG_PARAMS
    return transforms.Compose([
        AutoCropBorders(),
        # Rotate before cropping. Rotating last leaves black triangular corners,
        # reintroducing the border artifact AutoCropBorders exists to remove; the
        # subsequent crop trims them off instead.
        transforms.RandomRotation(p["rotation_deg"]),
        transforms.RandomResizedCrop(p["output_size"], scale=tuple(p["zoom_range"]),
                                     ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(p["horizontal_flip_p"]),
        transforms.RandomVerticalFlip(p["vertical_flip_p"]),
        transforms.ColorJitter(
            brightness=p["brightness_range"][1] - 1.0,
            contrast=p["contrast_range"][1] - 1.0,
            saturation=0.0,
            hue=0.0,
        ),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_eval_transform() -> transforms.Compose:
    """Deterministic resize and normalise. Never augment val or test."""
    size = C.AUG_PARAMS["output_size"]
    return transforms.Compose([
        AutoCropBorders(),
        transforms.Resize((size, size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class PlantDiseaseDataset(Dataset):
    """Reads splits.csv. Set task='disease' or task='severity'.

    severity restricts to diseased rows, since healthy leaves have no severity.
    """

    def __init__(self, rows: pd.DataFrame, task: str = "disease", train: bool = False,
                 class_to_idx: dict[str, int] | None = None):
        if task not in ("disease", "severity"):
            raise ValueError(f"task must be 'disease' or 'severity', got {task!r}")
        if task == "severity":
            rows = rows[rows["category"] == "disease"]
        self.rows = rows.reset_index(drop=True)
        self.task = task
        self.target_col = "label" if task == "disease" else "severity"
        classes = sorted(self.rows[self.target_col].unique())
        self.class_to_idx = class_to_idx or {c: i for i, c in enumerate(classes)}
        self.transform = build_train_transform() if train else build_eval_transform()

    def __len__(self) -> int:
        return len(self.rows)

    @property
    def targets(self) -> list[int]:
        return [self.class_to_idx[v] for v in self.rows[self.target_col]]

    def __getitem__(self, i: int):
        row = self.rows.iloc[i]
        path = C.IMAGES_DIR / Path(row["image_path"]).name
        with Image.open(path) as img:
            img = img.convert("RGB")
            return self.transform(img), self.class_to_idx[row[self.target_col]]


def make_balanced_sampler(targets: list[int], full_parity: bool = False) -> WeightedRandomSampler:
    """Oversample minority classes so every class is equally likely per draw.

    full_parity=False draws len(targets) samples per epoch, which already gives
    equal per-class probability and keeps epochs cheap. full_parity=True draws
    n_classes * largest_class_count instead, so every class contributes the same
    absolute count per epoch; this matches strict hard-balancing but lengthens an
    epoch roughly 4.6x on this dataset.

    Pair with REBALANCE='sampler' and plain cross-entropy. Combining this with
    class-weighted loss over-corrects the minority classes.
    """
    counts = pd.Series(targets).value_counts()
    weights = [1.0 / counts[t] for t in targets]
    n = len(counts) * int(counts.max()) if full_parity else len(targets)
    return WeightedRandomSampler(torch.as_tensor(weights, dtype=torch.double),
                                 num_samples=n, replacement=True)


def class_weights(targets: list[int]) -> torch.Tensor:
    """Inverse-frequency weights for cross-entropy.

    The alternative to make_balanced_sampler, not a companion to it.
    """
    counts = pd.Series(targets).value_counts().sort_index()
    w = len(targets) / (len(counts) * counts.astype(float))
    return torch.as_tensor(w.values, dtype=torch.float)


def load_split(split: str | None = None, fold: int | None = None) -> pd.DataFrame:
    """Rows for a frozen split, or for a CV fold.

    fold=k returns train+val rows excluding fold k. Use split='test' only once,
    after model selection is frozen.
    """
    df = pd.read_csv(C.SPLITS)
    if fold is not None:
        tv = df[df.split != "test"]
        return tv[tv.fold != fold] if split == "train" else tv[tv.fold == fold]
    return df[df.split == split] if split else df
