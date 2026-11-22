"""Sanity-check your trained model files:  python -m scripts.check_model "where is my refund?" """
import sys

from app.config import get_settings
from app.services.classifier.factory import build_classifier

s = get_settings()
clf = build_classifier(s.classifier_backend, s.model_dir)
print("backend:", clf.name, "| labels:", clf.labels())
for text in sys.argv[1:] or ["wheres my refnd?? its been 2 wks", "cant login forgot pw", "need invoice for march"]:
    p = clf.predict(text)
    print(f"{p.label:14s} {p.confidence:.2f}  <- {text}")
