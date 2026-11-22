# NOTES

**Built:** customer form + team dashboard (React/Vite/TS), FastAPI service layer, Supabase tables, DistilBERT category classifier (ONNX default), FAQ-grounded draft replies.

## Decisions and trade-offs
- **Category is team-only.** The customer gets only the ticket ID and a confirmation. The model can be wrong or UNCLEAR, a visible wrong label confuses customers, and priority/draft are internal. Trade-off: less transparency for the customer.
- **Layers:** routes (HTTP only) -> services (`TicketService`, `ClassificationService`, `DraftService`) -> repository port (Supabase / in-memory). Services have no FastAPI imports, so tests use a stub classifier, a fake LLM and the memory repo (no DB, no model needed).
- **Validation twice:** browser (instant feedback) and Pydantic (the real guard). Both use the same limits (name 1-100, message 10-2000). Server errors share one JSON shape and are shown beside each field, or in a banner when not field-specific.
- **ONNX by default:** onnxruntime + `tokenizers` only (no torch), faster and smaller to deploy. safetensors/joblib stay as fallbacks. Confidence below `UNCLEAR_BELOW` becomes `UNCLEAR` for manual triage.
- **Drafts run in a background task**, so the customer never waits for the LLM; the drawer polls while `pending`. Trade-off: a restart loses pending drafts (next: queue + retry).
- **Grounding in layers:** retrieval threshold (no FAQ => fixed "no matching FAQ" text, LLM not called) -> prompt rules (ticket text is untrusted data) -> output guards (valid JSON, cited ids must be retrieved ids, no "refund approved" claims) -> human review. Injection phrases are also removed from the retrieval query and flagged in the UI.
- **Supabase:** backend-only service-role key; RLS on with no policies.
- **Priority is rule-based** (no priority labels exist). Customers can game it by typing "URGENT".

## Where the AI tool gave wrong output
1. _TODO (you): write a real case from your own work, and how you caught it._
2. _TODO (you): second real case._

## Known limits
Retrieval is TF-IDF (misses paraphrases; threshold needs tuning on your FAQ); BANNED-phrase check is a heuristic; no rate limiting; single shared team login; no accent/Sinhala handling.

## With one more week
Embedding/hybrid retrieval + reranker; Redis queue with retries; real users table (hashed passwords) and rate limits; golden-set CI for draft quality (incl. injections); calibrate the `UNCLEAR` threshold; Playwright E2E; evaluate with a real LLM and publish the B3 table.
