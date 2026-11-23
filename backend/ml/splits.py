"""Group-aware, stratified train/val/test split. Single source of truth for sklearn AND DistilBERT training."""
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from ml.groups import near_dup_groups


def make_splits(df, seed: int = 42, thr: float = 0.9):
    """df needs columns: norm, category.  Returns (train_idx, val_idx, test_idx, groups)."""
    y = df["category"].values
    groups = near_dup_groups(df["norm"].tolist(), thr=thr)
    sizes = np.bincount(groups)
    print(f"near-dup groups: {len(sizes)} | largest group: {sizes.max()} rows ({sizes.max() / len(df):.1%})")

    outer = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=seed)
    trval, test = next(outer.split(df, y, groups))
    inner = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    tr_rel, val_rel = next(inner.split(df.iloc[trval], y[trval], groups[trval]))
    train, val = trval[tr_rel], trval[val_rel]

    # --- leak checks: these are the proof that the test score is honest ---
    assert not (set(groups[train]) & set(groups[test])), "group leak train/test"
    assert not (set(groups[val]) & set(groups[test])), "group leak val/test"
    assert not (set(df["norm"].iloc[train]) & set(df["norm"].iloc[test])), "text leak train/test"
    print("split sizes (train/val/test):", len(train), len(val), len(test))
    return train, val, test, groups
