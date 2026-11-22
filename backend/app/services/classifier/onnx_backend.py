from pathlib import Path

import numpy as np

from .base import Prediction, load_labels, softmax


class OnnxClassifier:
    """DistilBERT exported to ONNX. Needs: *.onnx, tokenizer.json, labels.json (or config.json id2label).
    Light-weight: onnxruntime + tokenizers only (no torch / transformers)."""
    name = "onnx"

    def __init__(self, model_dir: str, max_length: int = 128) -> None:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        d = Path(model_dir)
        onnx_files = sorted(d.glob("*.onnx"))
        if not onnx_files:
            raise FileNotFoundError(f"No .onnx file in {d}")
        self._labels = load_labels(d)
        self._tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        self._tok.enable_truncation(max_length=max_length)
        so = ort.SessionOptions()
        so.log_severity_level = 3
        self._sess = ort.InferenceSession(str(onnx_files[0]), sess_options=so, providers=["CPUExecutionProvider"])
        self._inputs = {i.name for i in self._sess.get_inputs()}

    def labels(self) -> list[str]:
        return self._labels

    def predict(self, text: str) -> Prediction:
        enc = self._tok.encode(text)
        ids = np.array([enc.ids], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": np.array([enc.attention_mask], dtype=np.int64)}
        if "token_type_ids" in self._inputs:
            feeds["token_type_ids"] = np.zeros_like(ids)
        logits = self._sess.run(None, {k: v for k, v in feeds.items() if k in self._inputs})[0][0]
        probs = softmax(np.asarray(logits, dtype=np.float64))
        i = int(probs.argmax())
        return Prediction(self._labels[i], float(probs[i]))
