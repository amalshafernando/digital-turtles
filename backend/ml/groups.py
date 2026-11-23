import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer


def near_dup_groups(texts, thr: float = 0.9, chunk: int = 1000) -> np.ndarray:
    """Texts with cosine >= thr end up in the same group (connected components).
    CHECK the largest group: a giant component means thr is too low (raise it)."""
    X = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform(texts)   # rows are L2-normalised
    XT = X.T.tocsr()
    n = X.shape[0]
    rows, cols = [np.array([], dtype=int)], [np.array([], dtype=int)]
    for s in range(0, n, chunk):
        S = (X[s:s + chunk] @ XT).tocoo()
        keep = (S.data >= thr) & (S.row + s != S.col)
        rows.append(S.row[keep] + s)
        cols.append(S.col[keep])
    r, c = np.concatenate(rows), np.concatenate(cols)
    G = sp.coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n))
    _, labels = connected_components(G, directed=False)
    return labels
