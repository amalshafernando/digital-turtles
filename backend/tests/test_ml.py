import json
import random
from pathlib import Path

import pytest

from app.textclean import clean_text
from ml.data import clean_frame
from ml.groups import near_dup_groups
from ml.train import run


def test_clean_text_removes_placeholders():
    assert "{{" not in clean_text("Cancel {{Order Number}} NOW!!")
    assert clean_text("  WHERE is   my refund?? ") == "where is my refund"


def test_near_duplicates_share_a_group():
    g = near_dup_groups(["cancel my order", "cancel my order please", "where is my refund"], thr=0.6)
    assert g[0] == g[1] and g[0] != g[2]


def _synthetic():
    import pandas as pd
    rnd = random.Random(0)
    pools = {"REFUND": "refund money back return reimburse credit",
             "ORDER": "order cancel track package purchase placed",
             "ACCOUNT": "password login account username profile sign",
             "INVOICE": "invoice receipt bill statement vat pdf"}
    filler = [f"w{i}" for i in range(400)]
    rows = []
    for cat, words in pools.items():
        w = words.split()
        for _ in range(90):
            toks = rnd.sample(w, 3) + rnd.sample(filler, 5)
            rnd.shuffle(toks)
            rows.append({"text": " ".join(toks), "category": cat, "intent": cat.lower()})
    rows.append({"text": "cancel {{Order Number}}", "category": "ORDER", "intent": "x"})
    rows.append({"text": "cancel {{Order Number}}", "category": "REFUND", "intent": "y"})   # conflicting label
    return pd.DataFrame(rows)


def test_training_pipeline_end_to_end_on_synthetic_data(tmp_path):
    df = clean_frame(_synthetic())
    assert not df["norm"].eq("cancel").any()            # the conflicting pair was dropped
    m = run(df, out_dir=tmp_path, Cs=(1, 10))           # asserts inside make_splits prove there is no group leak
    assert m["test_accuracy"] > 0.7
    assert (tmp_path / "model.joblib").exists() and json.loads((tmp_path / "metrics.json").read_text())["n_test"] > 0


@pytest.mark.skipif(not Path("models/model.joblib").exists(), reason="no joblib model in models/")
def test_real_joblib_model_outputs_valid_probabilities():
    import joblib
    m = joblib.load("models/model.joblib")
    p = m.predict_proba(["wheres my refnd"])[0]
    assert abs(p.sum() - 1) < 1e-6 and m.predict(["wheres my refnd"])[0] in set(m.classes_)
