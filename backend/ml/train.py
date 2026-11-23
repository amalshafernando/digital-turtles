"""TF-IDF + LogisticRegression baseline (B1).   Run from backend/:  python -m ml.train
Output: ml/artifacts/model.joblib + metrics.json   (copy model.joblib to models/ to serve it).
Hyper-parameters are chosen on VALIDATION; the TEST set is scored exactly once at the end."""
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline

from app.textclean import clean_text
from ml.splits import make_splits

OUT = Path("ml/artifacts")


def make_pipe(C: float) -> Pipeline:
    feats = FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(preprocessor=clean_text, analyzer="char_wb", ngram_range=(3, 5),
                                 min_df=3, sublinear_tf=True, max_features=120_000)),   # typo tolerance
    ])
    return Pipeline([("features", feats), ("clf", LogisticRegression(C=C, max_iter=3000))])


def run(df, out_dir: Path = OUT, Cs=(1, 10, 30), seed: int = 42, thr: float = 0.9) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    X, y = df["text"].values, df["category"].values
    train, val, test, _ = make_splits(df, seed, thr)
    trval = list(train) + list(val)

    best_C, best_f1 = None, -1.0
    for C in Cs:                                              # validation only, never the test set
        p = make_pipe(C).fit(X[train], y[train])
        f1 = f1_score(y[val], p.predict(X[val]), average="macro")
        print(f"C={C}: val macro-F1={f1:.4f}")
        if f1 > best_f1:
            best_C, best_f1 = C, f1

    final = make_pipe(best_C).fit(X[trval], y[trval])
    pred = final.predict(X[test])                              # TEST: once
    metrics = {"best_C": best_C, "seed": seed, "near_dup_threshold": thr,
               "n_train_val": len(trval), "n_test": int(len(test)),
               "test_accuracy": float(accuracy_score(y[test], pred)),
               "test_macro_f1": float(f1_score(y[test], pred, average="macro"))}
    print(json.dumps(metrics, indent=2))
    print(classification_report(y[test], pred, digits=3))
    joblib.dump(final, out_dir / "model.joblib", compress=3)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    from ml.data import load_clean
    run(load_clean())


if __name__ == "__main__":
    main()
