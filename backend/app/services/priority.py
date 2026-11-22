"""Rule-based priority. The dataset has no priority labels, so this is a transparent heuristic."""
HIGH_WORDS = ("urgent", "asap", "immediately", "fraud", "unauthorized", "unauthorised", "hacked", "stolen",
              "charged twice", "double charged", "cant log in", "can't log in", "cannot log in", "locked out")
MEDIUM_CATEGORIES = {"PAYMENT", "REFUND"}


def score_priority(text: str, category: str) -> str:
    t = text.lower()
    score = 2 if any(w in t for w in HIGH_WORDS) else 0
    if category.upper() in MEDIUM_CATEGORIES:
        score += 1
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 15 and sum(c.isupper() for c in letters) / len(letters) > 0.6:
        score += 1
    if text.count("!") >= 3:
        score += 1
    return "high" if score >= 3 else "medium" if score >= 1 else "low"
