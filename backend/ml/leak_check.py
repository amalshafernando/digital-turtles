"""Quantitative evidence that the group split does not leak:  python -m ml.leak_check
Compares RANDOM split vs GROUP split: (a) share of test texts having a near-duplicate in train, (b) test score."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from ml.splits import make_splits
from ml.train import make_pipe


def max_sim_to_train(train_texts, test_texts, chunk: int = 1000) -> np.ndarray:
    v = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(train_texts)
    B = v.transform(train_texts).T.tocsr()
    A = v.transform(test_texts)
    best = np.zeros(A.shape[0])
    for s in range(0, A.shape[0], chunk):
        best[s:s + chunk] = (A[s:s + chunk] @ B).max(axis=1).toarray().ravel()
    return best


def report(name, df, tr, te, thr=0.9):
    sims = max_sim_to_train(df["norm"].iloc[tr].tolist(), df["norm"].iloc[te].tolist())
    p = make_pipe(10).fit(df["text"].values[tr], df["category"].values[tr])
    pred = p.predict(df["text"].values[te])
    y = df["category"].values[te]
    print(f"{name:7s} | test with >= {thr} neighbour in train: {(sims >= thr).mean():6.1%} | "
          f"median max-sim {np.median(sims):.2f} | acc {accuracy_score(y, pred):.4f} | macro-F1 {f1_score(y, pred, average='macro'):.4f}")


def main():
    from ml.data import load_clean
    df = load_clean()
    idx = np.arange(len(df))
    r_tr, r_te = train_test_split(idx, test_size=1 / 6, stratify=df["category"], random_state=42)
    report("random", df, r_tr, r_te)
    g_tr, g_val, g_te, _ = make_splits(df)
    report("group", df, np.concatenate([g_tr, g_val]), g_te)


if __name__ == "__main__":
    main()
