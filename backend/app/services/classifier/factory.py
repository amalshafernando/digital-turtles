import logging
from pathlib import Path

from .base import Classifier, Prediction

log = logging.getLogger("classifier")


class NullClassifier:
    """Used when no model files are found, so the app still runs (everything -> UNCLEAR)."""
    name = "none"

    def labels(self) -> list[str]:
        return []

    def predict(self, text: str) -> Prediction:
        return Prediction("UNCLEAR", 0.0)


def _try(factory, what: str):
    try:
        return factory()
    except Exception as e:  # noqa: BLE001  - we want to fall through to the next backend
        log.warning("classifier backend %s unavailable: %s", what, e)
        return None


def build_classifier(backend: str, model_dir: str) -> Classifier:
    d = Path(model_dir)

    def onnx():
        from .onnx_backend import OnnxClassifier
        return OnnxClassifier(model_dir)

    def hf():
        from .hf_backend import HfClassifier
        return HfClassifier(model_dir)

    def jl():
        from .joblib_backend import JoblibClassifier
        return JoblibClassifier(model_dir)

    order = {"onnx": [("onnx", onnx)], "hf": [("hf", hf)], "joblib": [("joblib", jl)],
             "none": [], "auto": [("onnx", onnx), ("joblib", jl), ("hf", hf)]}[backend]
    for name, fn in order:
        clf = _try(fn, name)
        if clf is not None:
            log.info("classifier backend: %s (%d labels)", clf.name, len(clf.labels()))
            return clf
    log.warning("No classifier loaded from %s - tickets will be categorised UNCLEAR.", d.resolve())
    return NullClassifier()
