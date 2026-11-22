from pathlib import Path

from .base import Prediction


class JoblibClassifier:
    """A scikit-learn estimator/pipeline saved with joblib that accepts RAW TEXT and supports
    predict_proba (e.g. TF-IDF + LogisticRegression). Used as a light fallback."""
    name = "joblib"

    def __init__(self, model_dir: str) -> None:
        import joblib

        path = Path(model_dir) / "model.joblib"
        if not path.exists():
            raise FileNotFoundError(path)
        self._model = joblib.load(path)
        if not hasattr(self._model, "predict_proba"):
            raise TypeError("model.joblib must expose predict_proba(texts)")

    def labels(self) -> list[str]:
        return [str(c) for c in self._model.classes_]

    def predict(self, text: str) -> Prediction:
        proba = self._model.predict_proba([text])[0]
        i = int(proba.argmax())
        return Prediction(str(self._model.classes_[i]), float(proba[i]))
