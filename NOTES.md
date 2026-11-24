# NOTES

## What I built

I built a full-stack Smart Support Desk with ticket classification and AI-assisted reply drafting.

For the ticket classifier, I trained a Logistic Regression baseline with TF-IDF and fine-tuned a DistilBERT model on Google Colab using the customer support dataset. DistilBERT gave the best results and highest accuracy across experiments, so I selected it as the primary model and exported it to ONNX for lightweight runtime serving. All training notebooks, exported models, and experiment codes are available in this Google Drive folder: [Google Drive Folder](https://drive.google.com/drive/folders/1QDKUnNE2QEa7q5nNOda4F5A7fLbmEyOG). In addition, I added a copy of the exact same notebook inside this repository at [`backend/notebook/destilbert-finetune-and-inference.ipynb`](backend/notebook/destilbert-finetune-and-inference.ipynb).

The complete system features:
- **Frontend:** React + Vite + TypeScript customer portal and protected team dashboard.
- **Backend:** FastAPI service with structured layers (API routes, services, repositories) and Supabase (Postgres) or in-memory persistence.
- **ML Ticket Classifier (B1):** DistilBERT fine-tuned on the Bitext dataset and exported to ONNX (with TF-IDF/Logistic Regression as baseline). Evaluated on a leak-free group split and tested on 20 real-style messy inputs.
- **AI Reply Drafts (B2):** FAQ-grounded drafts using Groq API (Llama 3.3 70B / 3.1 8B) with strict JSON output, prompt injection defense, and retrieval gating.
- **Redis Semantic Cache:** Caches recurring support queries by meaning to drastically reduce LLM token costs and cut response latency to under 10ms.
- **Single-Command Delivery (Part C):** Fully orchestrated via Docker Compose (Frontend, Backend, Redis) with healthchecks.

## Design choices

1. **Security & Boundary Isolation:** Customers receive only a ticket ID and confirmation. Category, priority, and AI drafts remain strictly internal to the team dashboard to prevent leaking unreviewed or hallucinated outputs.
2. **Defensive AI Pipeline:**
   - *Gate:* If no FAQ item scores above the retrieval threshold (`FAQ_MIN_SCORE`), the LLM is never called, saving tokens.
   - *Semantic Cache:* Redis caches embeddings and verified FAQ answers so repeated user questions hit cache with 0 LLM cost.
   - *Input/Output Guards:* Customer text is wrapped inside `<ticket>` tags and treated strictly as untrusted data; regex filters block unauthorized refund or policy commitment claims.
3. **Groq over Local Ollama/Heavy Providers:** Integrated Groq via clean, lightweight HTTP completions. This avoids heavy SDK dependencies and massive local GPU/memory footprints while providing ultra-fast inference (<500ms).

## Two places where AI output was wrong

1. **Hallucinated FAQ Path & Missing Assets:** An AI assistant suggested loading FAQ entries from `data/faq.json`, but the repository path was `backend/faq/faq.json`. I caught this during Docker build tests when the container crashed on startup due to a missing file error. I fixed `config.py` and ensured `backend/Dockerfile` copied the `faq/` directory properly.
2. **Dockerized Ollama Misconfiguration:** An AI tool suggested adding an Ollama service inside Docker Compose with local GPU passthrough. Upon inspecting resource overhead and startup times, running multi-gigabyte models in local containers proved impractical for take-home evaluation. I redirected the LLM provider architecture to Groq's high-speed API with fallback to `MockLLM` for automated unit tests.

## Trade-offs

- **ONNX Runtime vs. PyTorch:** Deployed the classifier using ONNX Runtime with tokenizers instead of PyTorch. This reduced the Docker image size by over 1.5 GB and eliminated GPU requirements at serving time, with negligible loss in inference latency.
- **TF-IDF Character N-Grams vs. Vector Search for FAQ:** Used character n-gram TF-IDF for FAQ retrieval to handle user typos without requiring an active external embedding API or large vector database.
- **Semantic Cache Threshold:** Set the similarity threshold at 0.90; higher values miss valid rephrasings, while lower values risk serving answers for subtly different inquiries.

## Measuring quality with 10,000 tickets per day

1. **Automated Metrics & Telemetry:** Log grounding accuracy, no-match percentage, FAQ citation match rate, prompt-injection flag frequency, and agent edit distance (how much the human agent modifies the AI draft before sending).
2. **Golden Benchmark Dataset:** Maintain a 500-ticket regression test suite with known ground truths. Run automated evaluations on every prompt, model, or FAQ change.
3. **Dual Review Sampling:** Sample 1% of daily tickets (100 tickets/day) for blind human evaluation (correct, partially correct, wrong) and monitor category confusion matrices over time.
4. **Cost & Latency Tracking:** Monitor Redis cache hit rate, token expenditure per ticket, and p95 latency.

## What I would do next with one more week

1. **Hybrid Retrieval (Dense + Sparse):** Combine TF-IDF with dense embeddings (e.g., FastEmbed/BGE) for even better FAQ retrieval semantic matching.
2. **Async Task Queue:** Move draft generation to an asynchronous Celery/Redis background worker queue to decouple API ticket creation from external LLM latency.
3. **Full CI/CD Pipeline:** Implement GitHub Actions with automated linting, test suites, Docker image container scans, and push to container registry (GHCR).
4. **Agent Analytics Dashboard:** Build analytics views tracking ticket volume trends, recurring customer pain points, and agent response times.
