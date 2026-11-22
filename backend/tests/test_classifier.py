import json

import pytest

from app.services.classification_service import ClassificationService
from app.services.classifier.base import Prediction, load_labels
from app.services.classifier.factory import NullClassifier, build_classifier


def test_load_labels_from_json_list_and_dict(tmp_path):
    (tmp_path / "labels.json").write_text(json.dumps(["B", "A"]))
    assert load_labels(tmp_path) == ["B", "A"]
    (tmp_path / "labels.json").write_text(json.dumps({"1": "X", "0": "Y"}))
    assert load_labels(tmp_path) == ["Y", "X"]


def test_generic_label_names_are_rejected(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"id2label": {"0": "LABEL_0", "1": "LABEL_1"}}))
    with pytest.raises(RuntimeError):
        load_labels(tmp_path)


def test_missing_model_files_fall_back_to_null_classifier(tmp_path):
    assert isinstance(build_classifier("auto", str(tmp_path)), NullClassifier)


def test_unclear_threshold():
    class C:
        name = "x"
        def labels(self): return ["A"]
        def predict(self, t): return Prediction("A", 0.2)
    assert ClassificationService(C(), 0.35).classify("hello")[0] == "UNCLEAR"
    assert ClassificationService(C(), 0.10).classify("hello")[0] == "A"
