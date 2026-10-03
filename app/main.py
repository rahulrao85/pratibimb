"""
Pratibimb FastAPI Application.
Exposes REST endpoints for:
- Senior profile & decision style (/api/senior)
- Mandate & limits table (/api/mandate)
- Vendors registry (/api/vendors)
- Contracts repository (/api/contracts)
- Decision ledger & history (/api/decisions)
- Lessons library (/api/lessons)
- Demo requests (/api/requests)
- Agentic verdict synthesis (/api/decide)
- Backtest evaluation (/api/backtest)
- Senior override ingestion (/api/learner/override)
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.models import VendorRequest, VerdictResponse
from agents.engine import PratibimbEngine
from agents.backtest import run_backtest

app = FastAPI(
    title="Pratibimb API",
    description="The AI mirror of a senior decision-maker for Google Cloud AI Builder Cup 2026",
    version="0.1.0"
)

# Enable CORS for React + Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data"
engine = PratibimbEngine(data_dir=DATA_DIR)

def load_json_file(filename: str) -> Dict[str, Any]:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pratibimb-engine",
        "model": "gemini-3.8-flash",
        "senior": "Meera Nair",
        "location": "Mumbai, India"
    }

@app.get("/api/senior")
def get_senior():
    return load_json_file("senior.json")

@app.get("/api/mandate")
def get_mandate():
    return load_json_file("mandate.json")

@app.get("/api/vendors")
def get_vendors():
    return load_json_file("vendors.json")

@app.get("/api/contracts")
def get_contracts():
    return load_json_file("contracts.json")

@app.get("/api/decisions")
def get_decisions(include_holdouts: bool = False):
    data = load_json_file("decisions.json")
    decisions = data.get("decisions", [])
    if not include_holdouts:
        decisions = [d for d in decisions if not d.get("holdout", False)]
    return {"decisions": decisions, "total": len(decisions)}

@app.get("/api/lessons")
def get_lessons():
    return load_json_file("lessons.json")

@app.get("/api/requests")
def get_requests():
    return load_json_file("requests.json")

@app.post("/api/decide", response_model=VerdictResponse)
def decide(request: VendorRequest):
    try:
        verdict = engine.decide(request.model_dump())
        return verdict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest")
def get_backtest():
    try:
        results = run_backtest(verbose=False)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OverridePayload(BaseModel):
    request_id: str
    engine_verdict: str
    senior_decision: str
    senior_override_note: str
    proposed_rule: str
    senior_name: Optional[str] = "Meera Nair"

@app.post("/api/learner/override")
def record_override(payload: OverridePayload):
    try:
        new_lesson = engine.learner_agent.record_override(
            request_id=payload.request_id,
            engine_verdict=payload.engine_verdict,
            senior_decision=payload.senior_decision,
            senior_override_note=payload.senior_override_note,
            proposed_rule=payload.proposed_rule,
            senior_name=payload.senior_name
        )
        return {"status": "success", "lesson": new_lesson}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
