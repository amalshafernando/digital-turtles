# Smart Support Desk

Support-desk web app with an ML category classifier (DistilBERT) and FAQ-grounded AI reply drafts.

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + TypeScript (custom CSS, no UI kit) |
| Backend | FastAPI, Pydantic v2 |
| Database | Supabase (Postgres) |
| Classifier | DistilBERT: ONNX (default) / safetensors / joblib |
| Reply drafts | TF-IDF FAQ retrieval + LLM (mock / Ollama / Anthropic) with guards |

```
frontend/   React app  (/ customer form, /team dashboard)
backend/
  app/api/            thin HTTP routes (no logic)
  app/services/       ticket_service, classification_service, classifier/*, draft_service, faq_retriever, llm, priority
  app/repositories/   supabase_repo, memory_repo (persistence port)
  data/faq.json       the FAQ the drafts are grounded in
  models/             <- put your trained model files here
  tests/  eval/  scripts/
supabase/schema.sql   database schema
```

## 1. Supabase (database)
1. Create a project at supabase.com.
2. SQL Editor -> paste `supabase/schema.sql` -> Run.
3. Project Settings -> API: copy the **Project URL** and the **service_role** key.
   The service key is a server secret: it only goes into the backend `.env`, never into the frontend.
   (RLS is enabled with no policies, so the public anon key cannot read tickets.)

## 2. Configure
```bash
cp .env.example .env      # fill SUPABASE_URL, SUPABASE_SERVICE_KEY, TEAM_PASSWORD, JWT_SECRET
```

## 3. Your trained model -> `backend/models/`
Put **all files of one format in the same folder** (flat):

| Backend | Files needed |
|---|---|
| `onnx` (default, light, no torch) | `model.onnx` + `tokenizer.json` + `labels.json` (or `config.json` with real `id2label`) |
| `hf` (safetensors) | `model.safetensors` + `config.json` + tokenizer files; `pip install -r requirements-hf.txt` |
| `joblib` | `model.joblib` (sklearn pipeline taking raw text, with `predict_proba`) |

`CLASSIFIER_BACKEND=auto` tries onnx -> joblib -> hf. With no model the app still runs (everything = `UNCLEAR`).

Export from Colab (after training):
```python
import json
trainer.save_model("out"); tokenizer.save_pretrained("out")        # model.safetensors, config.json, tokenizer.json
json.dump([model.config.id2label[i] for i in range(model.config.num_labels)], open("out/labels.json", "w"))
# ONNX:
from optimum.onnxruntime import ORTModelForSequenceClassification
ORTModelForSequenceClassification.from_pretrained("out", export=True).save_pretrained("out_onnx")   # model.onnx
```
**labels.json must list class names in the same order as the model's output ids** (id 0 first).
Check your files: `cd backend && python -m scripts.check_model "where is my refnd??"`

## 4. Run
```bash
# backend            (Python 3.11+)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs

# frontend (new terminal)
cd frontend && npm install && npm run dev      # http://localhost:5173  (proxies /api to :8000)
```
Docker: `docker compose up --build` -> app on http://localhost:8080 (models mounted from `backend/models`).

Team login: `TEAM_USER` / `TEAM_PASSWORD` from `.env` at http://localhost:5173/team

## 5. Tests / eval
```bash
cd backend && pip install -r requirements-dev.txt && pytest -q     # 24 tests: API, validation, drafts, classifier loading
python -m eval.run_eval          # B3: 10 test tickets -> eval/results.md (set LLM_PROVIDER to a real LLM!)
cd frontend && npm run typecheck && npm run build
```
The `mock` LLM only echoes the top FAQ entry; use it for tests/demos, **not** for evaluating reply quality.

## API
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/tickets` | no | 201 `{id, message}` · 422 field errors |
| POST | `/api/auth/login` | no | `{username, password}` -> JWT |
| GET | `/api/tickets?category=&status=` | yes | 400 for malformed category |
| GET | `/api/tickets/{id}` | yes | full ticket + draft + FAQ sources |
| PATCH | `/api/tickets/{id}` | yes | `{status}` |
| GET | `/api/categories` | yes | model labels + `UNCLEAR` |

Errors always look like `{"error": {"code", "message", "fields": [{"field", "message"}]}}`.
