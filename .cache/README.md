# .cache

Disk cache for Gemini responses (`llm/`) and embeddings (`emb/`), plus the local usage log and demo state.
Only this README is tracked. With an empty cache the app still works: the first run of each request calls Gemini
and caches the answer; identical requests after that are instant and free.
