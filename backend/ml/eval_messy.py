"""Score the SERVED classifier (onnx / joblib / hf) on YOUR hand-written messy messages.
   python -m ml.eval_messy [path/to/messy.csv]"""
import csv
import sys

from app.config import get_settings
from app.services.classifier.factory import build_classifier

path = sys.argv[1] if len(sys.argv) > 1 else "ml/data/messy_20.csv"
s = get_settings()
clf = build_classifier(s.classifier_backend, s.model_dir)
if clf.name == "none":
    sys.exit(f"No model found in {s.model_dir}/ - add your model files first.")

rows = list(csv.DictReader(open(path, encoding="utf-8")))
wrong = []
for r in rows:
    p = clf.predict(r["text"])
    if p.label != r["true_category"]:
        wrong.append((r["text"], r["true_category"], p.label, p.confidence))
ok = len(rows) - len(wrong)
print(f"backend={clf.name} | messy accuracy: {ok}/{len(rows)} = {ok / len(rows):.0%}")
for t, true, pred, conf in wrong:
    print(f"  WRONG  true={true:12s} pred={pred:12s} conf={conf:.2f}  <- {t}")
