"""Fine-tune DistilBERT on the SAME group-aware split used by the TF-IDF baseline, then export safetensors + ONNX.

Colab:  upload/clone this backend/ folder, then
  !pip -q install transformers datasets accelerate "optimum[onnxruntime]" scikit-learn scipy pandas
  %cd backend
  !python -m ml.colab_train_distilbert
Outputs:  out/ (model.safetensors, config.json, tokenizer files, labels.json, metrics.json)  and  out_onnx/ (model.onnx + tokenizer).
NOTE: written against recent transformers/optimum; if TrainingArguments rejects `eval_strategy`, use `evaluation_strategy` (older versions).
"""
import json
from pathlib import Path

import numpy as np
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          Trainer, TrainingArguments)

from ml.data import load_clean
from ml.splits import make_splits

BASE, OUT, OUT_ONNX, SEED = "distilbert-base-uncased", Path("out"), Path("out_onnx"), 42

df = load_clean()
train, val, test, _ = make_splits(df, SEED)            # identical split => results comparable with the baseline

labels = sorted(df["category"].unique())               # <- this order IS the model's output order
label2id = {l: i for i, l in enumerate(labels)}
id2label = {i: l for l, i in label2id.items()}

tok = AutoTokenizer.from_pretrained(BASE)


def to_ds(idx):
    d = Dataset.from_dict({"text": df["text"].iloc[idx].tolist(),
                           "label": [label2id[c] for c in df["category"].iloc[idx]]})
    return d.map(lambda b: tok(b["text"], truncation=True, max_length=128), batched=True, remove_columns=["text"])


ds = {"train": to_ds(train), "val": to_ds(val), "test": to_ds(test)}
model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=len(labels), id2label=id2label, label2id=label2id)


def metrics_fn(p):
    pred = np.argmax(p.predictions, axis=-1)
    return {"accuracy": accuracy_score(p.label_ids, pred), "macro_f1": f1_score(p.label_ids, pred, average="macro")}


args = TrainingArguments(str(OUT / "ckpt"), num_train_epochs=3, learning_rate=5e-5, seed=SEED,
                         per_device_train_batch_size=32, per_device_eval_batch_size=64,
                         eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                         metric_for_best_model="macro_f1", report_to="none")
trainer = Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["val"],
                  data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics_fn)
trainer.train()                                         # model selection uses VALIDATION only

test_metrics = trainer.evaluate(ds["test"], metric_key_prefix="test")   # TEST: once
print(test_metrics)

OUT.mkdir(exist_ok=True)
trainer.save_model(str(OUT)); tok.save_pretrained(str(OUT))
(OUT / "labels.json").write_text(json.dumps(labels))
(OUT / "metrics.json").write_text(json.dumps({k: float(v) for k, v in test_metrics.items() if isinstance(v, (int, float))}, indent=2))

from optimum.onnxruntime import ORTModelForSequenceClassification   # noqa: E402
ORTModelForSequenceClassification.from_pretrained(str(OUT), export=True).save_pretrained(str(OUT_ONNX))
tok.save_pretrained(str(OUT_ONNX)); (OUT_ONNX / "labels.json").write_text(json.dumps(labels))
print("Copy out_onnx/* (model.onnx, tokenizer.json, labels.json) into backend/models/")
