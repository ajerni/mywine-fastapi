# mywine-fastapi

This is the AI API backend for mywine.info

## Production AI use cases (wired to API)

| Use case | API endpoint | Model | Provider | Where defined | Config |
|---|---|---|---|---|---|
| Wine AI summaries | `POST /getaisummary` | `llama-3.1-8b-instant` | Groq | `groq_summary/summary.py` (line 45) | Hardcoded |
| Sommelier chat | `POST /chat` | `llama-3.1-8b-instant` | Groq | `chat/agents/groq_triage.py` (line 103) | Hardcoded |
| SQL generation | `POST /generate-sql` | `openai/gpt-oss-20b` (default) | Groq | `sql_generate/generate.py` (line 27) | Env var `GROQ_SQL_MODEL` (also in `.env_example`) |