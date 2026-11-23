"""ONE cleaning function used by training AND serving (prevents train/serve skew)."""
import re

_PLACEHOLDER = re.compile(r"\{\{.*?\}\}")   # Bitext templates like {{Order Number}}


def clean_text(s: str) -> str:
    s = s.lower()
    s = _PLACEHOLDER.sub(" ", s)            # a dataset artifact the model must not learn
    s = re.sub(r"[^a-z0-9\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()
