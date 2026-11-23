"""Pick FAQ_MIN_SCORE from data, not by guessing:  python -m eval.tune_threshold
Prints the top retrieval score of every ticket in eval/test_tickets.json, grouped by whether an FAQ SHOULD answer it.
Choose a threshold between the 'no_match' scores and the 'answer' scores (add more tickets to the json for a better estimate)."""
import json

from app.config import get_settings
from app.services.faq_retriever import FaqRetriever

r = FaqRetriever(get_settings().faq_path)
cases = json.load(open("eval/test_tickets.json", encoding="utf-8"))
groups = {"answer": [], "no_match": []}
for c in cases:
    top = r.search(c["text"], k=1)[0]
    groups[c["expect"]].append((top.score, top.id, c["text"]))
for k, rows in groups.items():
    print(f"\n== expect {k} ==")
    for s, i, t in sorted(rows):
        print(f"  {s:.2f}  {i:22s} {t}")
lo = min((s for s, *_ in groups["answer"]), default=0)
hi = max((s for s, *_ in groups["no_match"]), default=0)
print(f"\nlowest 'answer' score = {lo:.2f}, highest 'no_match' score = {hi:.2f}")
print("separable: pick a value in between" if lo > hi else "OVERLAP: improve FAQ wording / retrieval, or accept some errors")
