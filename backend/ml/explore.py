"""B1 step 1: LOOK AT THE DATA before training.   python -m ml.explore"""
import pandas as pd

from app.textclean import clean_text
from ml.data import load_raw

df = load_raw()
print(df.shape, df.columns.tolist())
print(df[["instruction", "category", "intent"]].sample(8, random_state=1).to_string())

print("\n# class balance"); print(df["category"].value_counts())
print(df.groupby("category")["intent"].nunique())

print("\n# intent -> category (does one intent map to one category?)")
print("intents spanning >1 category:", (df.groupby("intent")["category"].nunique() > 1).sum())
print(df.groupby("category")["intent"].unique().to_string())

df["text"] = df["instruction"]
df["words"] = df["text"].str.split().str.len()
print("\n# length"); print(df["words"].describe())
print("share with {{placeholder}}:", df["text"].str.contains(r"\{\{").mean())

df["norm"] = df["text"].map(clean_text)
print("\n# duplicates")
print("exact duplicate texts:", df.duplicated("text").sum())
print("duplicates after normalising:", df.duplicated("norm").sum())

print("\n# label conflicts (same normalised text, different category)")
g = df.groupby("norm")["category"].nunique()
print("conflicting texts:", (g > 1).sum())
print(df[df["norm"].isin(g[g > 1].index)].sort_values("norm")[["text", "category", "intent"]].head(20).to_string())

print("\n# noise / typos?")
print("non-ascii share:", df["text"].str.contains(r"[^\x00-\x7F]").mean())
print(df["flags"].value_counts().head(15))
