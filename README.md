# Smart Support Desk

Support-desk web app: React + Vite + TypeScript frontend, FastAPI backend, Supabase (Postgres), a DistilBERT ticket classifier
(ONNX / safetensors / joblib), FAQ-grounded AI reply drafts with Groq LLM integration, and Redis Semantic Caching.

- **Engineering Notes & Tradeoffs:** See [NOTES.md](NOTES.md) for design choices, evaluation results, AI verification, and scaling notes.
- **Architecture Diagrams:** See [docs/architecture.md](docs/architecture.md).

## Quick start (Single Command)
```bash
cp .env.example .env        # fill GROQ_API_KEY (or use mock), and Supabase/memory credentials
docker compose up --build   # app: http://localhost:8080   team page: http://localhost:8080/team   API docs: http://localhost:8000/docs
```
This builds and starts the whole stack in a single command:
1. **Frontend:** React + Vite SPA served via Nginx on port `8080` (with `/api/` reverse proxy).
2. **Backend:** FastAPI service on port `8000` with the DistilBERT ONNX classifier and FAQ draft service.
3. **Redis:** Caching service on port `6379` for semantic cache hits to minimize LLM cost.

Team login = `TEAM_USER` / `TEAM_PASSWORD` from `.env`. Put your model files in `backend/models/` first (see "Model files").

## Without Docker
```bash
# backend (Python 3.11+)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload                     # http://localhost:8000/docs

# frontend (second terminal)
cd frontend && npm install && npm run dev         # http://localhost:5173 (proxies /api -> :8000)
```
No Supabase yet? Try it with `REPOSITORY=memory` in `.env` (data is lost on restart).

## Supabase
1. Create a project at supabase.com.  2. SQL Editor -> paste `supabase/schema.sql` -> Run.
3. Project Settings -> API: copy the Project URL and the **service_role** key into `.env` (server-side secret, never in the frontend).
RLS is enabled with no policies, so the public anon key cannot read tickets.

## What's inside
```
frontend/                React app (/ customer form, /team dashboard + ticket drawer)
backend/app/api/         thin HTTP routes (no business logic)
backend/app/services/    ticket_service, classification_service, classifier/* (onnx|hf|joblib), draft_service, faq_retriever, llm, priority
backend/app/repositories supabase_repo, memory_repo (persistence port)
backend/app/textclean.py the ONE text-cleaning function for training and serving
backend/ml/              B1: explore, groups, splits, train (TF-IDF baseline), colab_train_distilbert, leak_check, eval_messy, REPORT.md
backend/faq/faq.json     the FAQ the drafts are grounded in
backend/eval/            B3: run_eval, tune_threshold, test_tickets.json
backend/tests/           API, validation, drafts, classifier loading, ML pipeline
supabase/schema.sql      database schema
docs/                    architecture (Mermaid), ai-mistakes log
```

## Model files (`backend/models/`)
| Backend | Files |
|---|---|
| `onnx` (default, no torch) | `model.onnx` + `tokenizer.json` + `labels.json` (or `config.json` with real `id2label`) |
| `hf` (safetensors) | `model.safetensors` + `config.json` + tokenizer files, and `pip install -r requirements-hf.txt` |
| `joblib` | `model.joblib` (sklearn pipeline on raw text with `predict_proba`) |

`CLASSIFIER_BACKEND=auto` tries onnx, then joblib, then hf. With no model the app still runs (everything becomes `UNCLEAR`).
`labels.json` must list classes in the model's output order (id 0 first). Verify: `cd backend && python -m scripts.check_model "wheres my refnd??"`.

## ML (B1)
Report template: `backend/ml/REPORT.md`. Run everything from `backend/` (`pip install -r requirements-dev.txt`):
```bash
python -m ml.explore         # look at the data first: duplicates, label conflicts, doubtful labels
python -m ml.train           # TF-IDF + LR baseline on a GROUP-aware split -> ml/artifacts/{model.joblib,metrics.json}
python -m ml.leak_check      # random vs group split: near-duplicate share + score (evidence of no leak)
python -m ml.eval_messy      # score the SERVED model on ml/data/messy_20.csv
```
DistilBERT: run `ml/colab_train_distilbert.py` in Colab (same split, so scores are comparable), then copy `out_onnx/*` into `backend/models/`.
`ml/data/messy_20.csv` has 8 starter rows: **write the other 12 yourself, before running the model.**

## AI drafts (B2 / B3)
Retrieval gate (no FAQ above `FAQ_MIN_SCORE` => fixed "no matching FAQ" text, LLM not called) -> Redis semantic cache check (cuts latency and token cost for recurring queries) -> prompt rules (ticket text is untrusted data) ->
output guards (valid JSON, cited ids must be retrieved ids, no "refund approved" claims) -> human review in the UI. Injection phrases are stripped from the retrieval query and flagged to the agent.
```bash
python -m eval.tune_threshold   # choose FAQ_MIN_SCORE from data
python -m eval.run_eval         # 10 test tickets -> eval/results.md (use a REAL LLM; mock only echoes the FAQ). Fill the verdict/reason columns by hand.
```
- `LLM_PROVIDER=groq`: Fastest, cost-effective inference (`GROQ_API_KEY` + `LLM_MODEL=llama-3.3-70b-versatile`).
- `LLM_PROVIDER=ollama`: Local model support (`docker compose --profile llm up`).
- `LLM_PROVIDER=anthropic`: Claude model support (`LLM_MODEL` + `ANTHROPIC_API_KEY`).
- `LLM_PROVIDER=mock`: Deterministic key-free mock for tests.

## Tests
```bash
cd backend && pytest -q                       # 28 tests (+1 skipped unless models/model.joblib exists)
cd frontend && npm run typecheck && npm run build
```

## API
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/tickets` | no | 201 `{id, message}` (category/draft stay internal) - 422 field errors |
| POST | `/api/auth/login` | no | `{username, password}` -> JWT |
| GET | `/api/tickets?category=&status=&limit=50&offset=0` | yes | 400 for malformed category |
| GET | `/api/tickets/{id}` | yes | full ticket + draft + FAQ sources |
| PATCH | `/api/tickets/{id}` (alias `/api/tickets/{id}/status`) | yes | `{status}` |
| GET | `/api/categories` | yes | model labels + `UNCLEAR` |
| GET | `/health`, `/api/health` | no | liveness (the second also shows backend names) |

Errors always look like `{"error": {"code", "message", "fields": [{"field", "message"}]}}`.

## Config (`.env.example`, no real secrets)
`REPOSITORY, SUPABASE_URL, SUPABASE_SERVICE_KEY, TEAM_USER, TEAM_PASSWORD, JWT_SECRET, CLASSIFIER_BACKEND, UNCLEAR_BELOW, LLM_PROVIDER, LLM_MODEL, OLLAMA_URL, ANTHROPIC_API_KEY, FAQ_MIN_SCORE, CORS_ORIGINS`
