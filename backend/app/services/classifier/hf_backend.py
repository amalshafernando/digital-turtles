from pathlib import Path

from .base import Prediction


class HfClassifier:
    """Serves the .safetensors checkpoint through transformers + torch (heavier; optional).
    Folder needs: config.json, model.safetensors, tokenizer files."""
    name = "hf"

    def __init__(self, model_dir: str, max_length: int = 128) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        d = Path(model_dir)
        self._torch = torch
        self._tok = AutoTokenizer.from_pretrained(d)
        self._model = AutoModelForSequenceClassification.from_pretrained(d).eval()
        self._max = max_length
        id2label = self._model.config.id2label
        self._labels = [id2label[i] for i in range(len(id2label))]
        if all(l.startswith("LABEL_") for l in self._labels):
            from .base import load_labels
            self._labels = load_labels(d)

    def labels(self) -> list[str]:
        return self._labels

    def predict(self, text: str) -> Prediction:
        enc = self._tok(text, return_tensors="pt", truncation=True, max_length=self._max)
        with self._torch.no_grad():
            probs = self._torch.softmax(self._model(**enc).logits[0], dim=-1)
        i = int(probs.argmax())
        return Prediction(self._labels[i], float(probs[i]))
