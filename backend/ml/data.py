import pandas as pd

from app.textclean import clean_text

DS = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"


def load_raw() -> pd.DataFrame:
    from datasets import load_dataset          # lazy: only needed for training
    return load_dataset(DS, split="train").to_pandas()


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Columns in: text, category, intent.  Out: same + norm, with conflicts and duplicates removed."""
    df = df.copy()
    df["norm"] = df["text"].map(clean_text)
    n_cat = df.groupby("norm")["category"].nunique()
    conflicts = set(n_cat[n_cat > 1].index)       # same text, different category -> truth unknown
    print(f"dropping {df['norm'].isin(conflicts).sum()} rows with conflicting labels")
    df = df[~df["norm"].isin(conflicts)]
    before = len(df)
    df = df.drop_duplicates("norm").reset_index(drop=True)
    print(f"dropped {before - len(df)} duplicate rows; {len(df)} remain")
    return df


def load_clean() -> pd.DataFrame:
    df = load_raw()[["instruction", "category", "intent"]].rename(columns={"instruction": "text"})
    return clean_frame(df)
