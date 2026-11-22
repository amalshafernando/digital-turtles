from .classifier.base import Classifier

UNCLEAR = "UNCLEAR"


class ClassificationService:
    """Wraps a Classifier backend + the 'I'm not sure' policy (low confidence -> UNCLEAR)."""

    def __init__(self, classifier: Classifier, unclear_below: float) -> None:
        self.classifier, self.unclear_below = classifier, unclear_below

    @property
    def backend(self) -> str:
        return self.classifier.name

    def classify(self, text: str) -> tuple[str, float]:
        p = self.classifier.predict(text)
        if p.confidence < self.unclear_below:
            return UNCLEAR, p.confidence
        return p.label, p.confidence

    def categories(self) -> list[str]:
        return sorted(self.classifier.labels()) + [UNCLEAR]
