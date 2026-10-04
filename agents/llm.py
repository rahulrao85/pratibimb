"""
Gemini access for Pratibimb.

One place that every agent goes through, so that:
- auth works the same locally (ADC, or the gcloud CLI token as a dev fallback) and on Cloud Run (service account);
- every response is cached on disk (re-running an identical prompt costs nothing);
- every call is logged with tokens and an estimated USD cost (see `cost_report`).

Set PRATIBIMB_LLM=off to run the deterministic rules only (the back-test baseline).
LLM_DAILY_CALL_CAP (default 300 live calls a day) protects the credit on a public deployment; past it, the
engine falls back to the rules and says so.
"""
from __future__ import annotations

import contextvars
import datetime as dt
import hashlib
import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env()

CACHE_DIR = Path(os.getenv("PRATIBIMB_CACHE_DIR", ROOT / ".cache" / "llm"))
USAGE_LOG = CACHE_DIR.parent / "usage.jsonl"

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# USD per 1M tokens (Gemini 3.8 Flash introductory list price). Thinking tokens bill as output.
PRICE_IN, PRICE_OUT = 0.75, 3.75
USD_TO_INR = 88
DAILY_CAP = int(os.getenv("LLM_DAILY_CALL_CAP", "300"))
# Tried in order if the main model is retired or unavailable (3.8 Flash is a short-availability model).
FALLBACK_MODELS = [m for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.7-flash,gemini-3.5-flash").split(",") if m]

_client = None
_lock = threading.Lock()
_today = {"day": None, "live": 0}
# Per-verdict meter: engine.decide() starts one; every call made for that verdict (in any thread that copied
# the context) adds its cost to it.
_meter: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar("pratibimb_meter", default=None)


class CapReached(RuntimeError):
    """The daily live-call cap is used up; callers fall back to the rules."""


def start_meter() -> list:
    m: list = []
    _meter.set(m)
    return m


def meter_total(m: list) -> dict:
    usd = sum(e["cost_usd"] for e in m)
    return {"live_calls": sum(not e["cached"] for e in m), "cached_calls": sum(e["cached"] for e in m),
            "cost_usd": round(usd, 5), "cost_inr": round(usd * USD_TO_INR, 2)}


def _metered(cached: bool, cost: float) -> None:
    m = _meter.get()
    if m is not None:
        m.append({"cached": cached, "cost_usd": cost})


def _take_live_slot() -> None:
    with _lock:
        day = dt.date.today().isoformat()
        if _today["day"] != day:
            _today.update(day=day, live=0)
        if _today["live"] >= DAILY_CAP:
            raise CapReached(f"daily cap of {DAILY_CAP} live Gemini calls reached")
        _today["live"] += 1


def calls_today() -> dict:
    return {"day": _today["day"], "live_calls": _today["live"], "cap": DAILY_CAP}


def _is_model_error(e: Exception) -> bool:
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return code in (404, 400) and "model" in str(e).lower()


def _tracer():
    from opentelemetry import trace

    return trace.get_tracer("pratibimb")


def enabled() -> bool:
    return os.getenv("PRATIBIMB_LLM", "on").lower() not in ("off", "0", "false", "rules")


PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "pratibimb-aibc")


class _GcloudCredentials:
    """Dev-only fallback when no ADC file exists: borrow the gcloud CLI's access token."""

    def __new__(cls):
        import google.auth.credentials as gac

        class Creds(gac.Credentials):
            def refresh(self, request):  # noqa: D401
                account = os.getenv("GCLOUD_ACCOUNT", "rahulrao85@gmail.com")
                tok = subprocess.run(
                    ["gcloud", "auth", "print-access-token", f"--account={account}"],
                    capture_output=True, text=True, shell=os.name == "nt", check=True,
                ).stdout.strip()
                self.token = tok
                self.expiry = dt.datetime.utcnow() + dt.timedelta(minutes=50)

        c = Creds()
        c._quota_project_id = PROJECT  # bill API calls to our project, not gcloud's own OAuth client
        c.refresh(None)
        return c


_client_lock = threading.Lock()
_creds = None


def credentials():
    """One credential for Vertex AI and Firestore: the attached service account on Cloud Run, else ADC, else gcloud."""
    global _creds
    if _creds is None:
        with _client_lock:
            if _creds is None:
                try:
                    import google.auth

                    _creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                except Exception:
                    _creds = _GcloudCredentials()
    return _creds


def client():
    global _client
    if _client is not None:
        return _client
    c = _make_client()  # outside the lock: credentials() takes it too
    with _client_lock:  # agents run in parallel: keep exactly one client
        if _client is None:
            _client = c
    return _client


def _make_client():
    from google import genai

    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        return genai.Client(vertexai=True, project=PROJECT, location=location, credentials=credentials())
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def warm_up() -> None:
    """Build the client and authenticate once (a free metadata call) so the first verdict isn't slow."""
    try:
        client().models.get(model=MODEL)
    except Exception:
        pass


def _log(entry: dict) -> None:
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _lock, open(USAGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def generate_json(
    agent: str,
    system: str,
    prompt: str,
    schema: Type[BaseModel],
    thinking: str = "LOW",
    temperature: Optional[float] = None,
) -> BaseModel:
    """Call Gemini with a Pydantic schema and return a validated instance (cached)."""
    from google.genai import types

    key_src = json.dumps(
        {"m": MODEL, "s": system, "p": prompt, "schema": schema.model_json_schema(), "t": thinking, "temp": temperature},
        sort_keys=True,
    )
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    path = CACHE_DIR / f"{agent}-{key}.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        _log({"ts": dt.datetime.now().isoformat(timespec="seconds"), "agent": agent, "cached": True, "cost_usd": 0.0})
        _metered(True, 0.0)
        return schema.model_validate(cached["output"])

    _take_live_slot()
    cfg_kwargs = dict(
        system_instruction=system,
        response_mime_type="application/json",
        response_json_schema=schema.model_json_schema(),
        thinking_config=types.ThinkingConfig(thinking_level=thinking),
        temperature=temperature,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    resp, used_model = None, MODEL
    with _tracer().start_as_current_span(f"gemini.{agent}") as span:
        span.set_attribute("gen_ai.request.model", MODEL)
        for model in [MODEL] + FALLBACK_MODELS:
            try:
                resp = client().models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(**cfg_kwargs))
                used_model = model
                break
            except Exception as e:  # model retired / unavailable: try the next one, re-raise after the last
                if model == ([MODEL] + FALLBACK_MODELS)[-1] or not _is_model_error(e):
                    raise
        span.set_attribute("gen_ai.response.model", used_model)

    out = schema.model_validate_json(resp.text)

    u = resp.usage_metadata
    tin = u.prompt_token_count or 0
    tout = (u.candidates_token_count or 0) + (getattr(u, "thoughts_token_count", 0) or 0)
    cost = (tin * PRICE_IN + tout * PRICE_OUT) / 1_000_000
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"agent": agent, "model": MODEL, "output": out.model_dump()}, ensure_ascii=False, indent=1), encoding="utf-8")
    _log({"ts": dt.datetime.now().isoformat(timespec="seconds"), "agent": agent, "cached": False, "model": used_model,
          "tokens_in": tin, "tokens_out": tout, "cost_usd": round(cost, 6)})
    _metered(False, cost)
    return out


def cost_report() -> dict:
    """Totals from the usage log (live calls only cost money)."""
    if not USAGE_LOG.exists():
        return {"live_calls": 0, "cached_calls": 0, "cost_usd": 0.0, "cost_inr": 0.0}
    live = cached = 0
    usd = 0.0
    for line in USAGE_LOG.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("cached"):
            cached += 1
        else:
            live += 1
            usd += e.get("cost_usd", 0.0)
    return {"live_calls": live, "cached_calls": cached, "cost_usd": round(usd, 4), "cost_inr": round(usd * USD_TO_INR, 2)}


if __name__ == "__main__":
    print(json.dumps(cost_report(), indent=2))


EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-2")
EMBED_DIR = CACHE_DIR.parent / "emb"
EMBED_PRICE_PER_M = 0.15  # USD per 1M input tokens (approx.; ~4 chars per token)


def embed(text: str, task: str = "RETRIEVAL_DOCUMENT", dims: int = 768) -> list:
    """Vertex AI text embedding (gemini-embedding-2), cached on disk: each text is embedded once."""
    from google.genai import types

    key = hashlib.sha256(json.dumps({"m": EMBED_MODEL, "t": text, "k": task, "d": dims}).encode("utf-8")).hexdigest()[:24]
    path = EMBED_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    _take_live_slot()
    with _tracer().start_as_current_span("gemini.embed"):
        vec = client().models.embed_content(model=EMBED_MODEL, contents=text,
                                            config=types.EmbedContentConfig(task_type=task, output_dimensionality=dims)).embeddings[0].values
    EMBED_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(vec)), encoding="utf-8")
    cost = len(text) / 4 * EMBED_PRICE_PER_M / 1_000_000
    _log({"ts": dt.datetime.now().isoformat(timespec="seconds"), "agent": "embed", "cached": False, "model": EMBED_MODEL,
          "tokens_in": len(text) // 4, "tokens_out": 0, "cost_usd": round(cost, 7)})
    _metered(False, cost)
    return list(vec)


def cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0
