"""B3: run drafts on the 10 hard test tickets and write eval/results.md.
   python -m eval.run_eval      (use a REAL LLM via LLM_PROVIDER for meaningful results; mock just echoes the FAQ)
The 'verdict' and 'reason' columns are for YOU to fill in by hand after reading each draft."""
import json
import time

from app.config import get_settings
from app.container import build_container

s = get_settings()
svc = build_container(s.model_copy(update={"repository": "memory"})).tickets.drafts
from app.services.draft_service import BANNED  # noqa: E402

cases = json.load(open("eval/test_tickets.json", encoding="utf-8"))
rows = [f"LLM: provider={s.llm_provider} model={s.llm_model or '-'} | min_score={s.faq_min_score}\n",
        "| # | kind | ticket | draft | sources | auto-checks | verdict (manual) | reason (manual) |",
        "|---|---|---|---|---|---|---|---|"]
for c in cases:
    t0 = time.time()
    d = svc.generate(c["text"])
    ms = int((time.time() - t0) * 1000)
    used = [x["id"] for x in d.sources]
    checks = {"abstain": (d.status == "no_match") == (c["expect"] == "no_match"),
              "sources": set(c["expect_faq"]) <= set(used) if c["expect"] == "answer" else used == [],
              "no_promise": not BANNED.search(d.text or "")}
    ok = " ".join(("PASS " if v else "FAIL ") + k for k, v in checks.items())
    txt = (d.text or "<failed>").replace("|", "/").replace("\n", " ")
    rows.append(f"| {c['id']} | {c['kind']} | {c['text']} | {txt} | {', '.join(used) or '-'} | {ok} ({ms}ms) |  |  |")
open("eval/results.md", "w", encoding="utf-8").write("\n".join(rows))
print("\n".join(rows))
