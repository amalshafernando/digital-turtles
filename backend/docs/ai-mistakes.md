# Log of places where the AI tool was wrong
Write each case the moment you see it (what it gave, how you found it, the fix). NOTES.md uses two of them. Only real cases.

1. An AI-generated suggestion used `data/faq.json`, but the real FAQ file was at `backend/faq/faq.json`. I checked `config.py`, the FAQ file, and Docker setup, then changed the setting to `faq/faq.json` and updated the Docker file.

2. An assistant claimed that Ollama was already included in Docker Compose. I checked `docker-compose.yml` and found that Ollama was missing. I did not treat that suggestion as complete.
