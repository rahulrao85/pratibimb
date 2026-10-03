# Pratibimb (प्रतिबिंब)

**The AI mirror of a senior decision-maker.**
Learns how a senior leader decides from past decisions, rationale, and subsequent outcomes — delivering audit-ready verdicts with mandatory citations while preserving human-in-the-loop authority.

Built for the **Google Cloud AI Builder Cup 2026 (JAPAC, Hack2skill)**  
*Theme:* Future of Work & Enterprise Productivity  
*Team:* Rahul Rao & Dipti (CA)

---

## Key Capabilities

1. **Mandate Guardrails:** Enforces the senior's exact delegation of authority limits.
2. **Episodic Precedent Retrieval:** Queries past decisions, weighting recent outcomes and penalizing repeated historical errors.
3. **Adversarial Contract Challenger:** Flags predatory auto-renewals, evergreen commitments, and missing liabilities against grounded contracts.
4. **Instinct Interviewer:** Generates targeted interrogatories mirroring the senior's risk mindset when critical operational parameters are absent.
5. **Continuous Learning Loop:** Ingests senior overrides and converts near-misses into enforceable governance lessons.

---

## Architecture & Directory Layout

```
pratibimb/
├── agents/             # Google ADK multi-agent system
│   ├── precedent.py    # Precedent retrieval & outcome evaluation
│   ├── challenger.py   # Adversarial contract clause verification
│   ├── interviewer.py  # Instinct question formulation
│   ├── decider.py      # Mandate logic & verdict synthesis
│   ├── learner.py      # Override ingestion & rule crystallization
│   └── engine.py       # Multi-agent orchestrator returning frozen verdict schema
├── app/                # FastAPI backend API
│   └── main.py         # REST endpoints for verdicts, backtest & lessons
├── data/               # Ground truth synthetic datasets
│   ├── senior.json     # Meera Nair's profile & decision style traits
│   ├── mandate.json    # Delegation of authority rule table
│   ├── vendors.json    # Master vendor registry
│   ├── contracts.json  # Full clause-level legal agreements
│   ├── decisions.json  # 40 episodic decisions (including 4 mistakes & 10 holdouts)
│   ├── lessons.json    # 6 governance lessons derived from outcomes
│   ├── requests.json   # 3 live benchmark demo requests
│   └── backtest.json   # 10 holdout cases for agreement evaluation
├── docs/               # Architecture, prompt engineering & data model
│   └── data-model.md
├── ui/                 # React + Vite frontend (Govu Aurora/Voltage Glassmorphism)
├── .env.example        # Environment variable specification
├── pyproject.toml      # Python 3.11 dependency configuration via uv
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11 via `uv`
- Node.js 18+ (for UI)
- Gemini API key (AI Studio free tier: `gemini-3.8-flash`)

### Local Setup
```bash
# Setup Python environment
uv venv --python 3.11
# Activate environment (Windows)
.venv\Scripts\activate
# Install dependencies
uv sync

# Run data validation & backtest harness
uv run python -m agents.backtest
```
