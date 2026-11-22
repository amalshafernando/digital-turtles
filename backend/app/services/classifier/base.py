import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass
class Prediction:
    label: str
    confidence: float


class Classifier(Protocol):
    name: str
    def predict(self, text: str) -> Prediction: ...
    def labels(self) -> list[str]: ...


def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


def load_labels(model_dir: Path) -> list[str]:
    """labels.json (list or {"0": "ACCOUNT", ...}) first, else config.json -> id2label."""
    lj = model_dir / "labels.json"
    if lj.exists():
        data = json.loads(lj.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return [data[k] for k in sorted(data, key=int)]
        return list(data)
    cj = model_dir / "config.json"
    if cj.exists():
        id2label = json.loads(cj.read_text(encoding="utf-8")).get("id2label")
        if id2label:
            labels = [id2label[k] for k in sorted(id2label, key=int)]
            if not all(l.startswith("LABEL_") for l in labels):
                return labels
    raise RuntimeError(
        f"No usable class names in {model_dir}. Add labels.json (e.g. [\"ACCOUNT\", \"ORDER\", ...] in the "
        "SAME order as training) or set id2label in config.json before exporting.")
