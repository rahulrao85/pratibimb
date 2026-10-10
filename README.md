# Pratibimb (प्रतिबिंब)

**The AI mirror of a senior decision-maker.**
Pratibimb learns how a senior decides from her past decisions, what happened afterwards, and her mistakes. It then
gives a first-level verdict on new requests the way she would, citing every rule, clause, precedent and lesson it relied on.
**The senior always makes the final call.** When she overrides a verdict, Pratibimb writes a lesson and files her decision
as a precedent, and the next verdict uses both.

**Live:** https://pratibimb-aibc.web.app (Firebase Hosting → Cloud Run, Singapore) ·
also https://pratibimb-88989965991.asia-southeast1.run.app and https://pratibimb.rahulrao.in

Built for the **Google Cloud AI Builder Cup 2026 (JAPAC, Hack2skill)** · Theme: Future of Work & Enterprise Productivity ·
Team: Rahul Rao & Dipti (CA). All data is synthetic.

## One company, three seniors, a Pratibimb for each

Meridian Global Services is a fictional Mumbai delivery centre serving clients across India, Singapore and Australia.
Leaders spend 37% of their time making decisions, and 61% say at least half of that time is ineffective (McKinsey, 1,259 leaders).
Pratibimb takes the routine, policy-bound part:

| Senior | Role | Decides | Indian/APAC practice in the data |
|---|---|---|---|
| **Meera Nair** | Head of Delivery Operations | vendor approvals (renewals, onboarding, one-time spend) | auto-renewal traps, client-data residency, key-person risk |
| **Vikram Sethi** | Head of Sales (India & APAC) | which leads and RFPs get a pursuit team | GeM/PSU buyers and L1 pricing, certification-based payment, column-fodder RFPs, free pilots |
| **Kavya Iyer** | Financial Controller | spend & payment exceptions (no PO, variances, overruns, advances) | GSTR-2B input credit, MSME 45-day rule (s.43B(h)), split invoices, bank-change fraud, March rush |

Same engine, same guardrails; each pack has its own senior profile, mandate (approval rules), 30 past decisions with
outcomes (4 of them mistakes that became lessons), documents and 15 held-out decisions. Packs live in `data/` (vendor)
and `data/packs/{leads,spend}/` (each has a `generate.py`). Adding a senior is adding a pack.

---

## How a verdict is made

Every verdict runs as a **Google ADK Workflow** (ADK 2.11 graph of nodes):

```
START → mandate → ┌ precedent   ┐ → gather (join) → decider
                  ├ challenger  ┤
                  └ interviewer ┘
```

- **mandate** (code): rules from `mandate.json` set the floor. Gemini may make the verdict stricter, never looser.
- **precedent / challenger / interviewer** (Gemini 3.8 Flash on Vertex AI, structured JSON) run in parallel: which past
  decisions and lessons apply; what the contract clauses hide (cited "CN-… §n"); the questions Meera would ask.
- **decider** (Gemini): a verdict inside the allowed set, with reasoning in Meera's voice. Every citation is checked against
  real IDs; invented ones are removed and listed. The decision file shows what Gemini proposed and what the mandate allowed.
- **learner**: when Meera overrides, Gemini drafts a lesson from her note, and her decision becomes precedent OVR-nnn.

**Memory:**
- What Meera teaches lives in **Cloud Firestore**, one sandbox per browser (cookie).
- Lessons survive restarts and new Cloud Run revisions, and never leak between visitors.
- The baseline memory (`decisions.json`, `lessons.json`) is read-only.

**Observability:** every workflow run is exported to **Cloud Trace** (ADK spans per node, plus one span per Gemini call),
and its trace ID and node timeline are returned with the verdict.

**Resilience:**
- Fallback models: `gemini-3.7-flash`, then `gemini-3.5-flash`.
- A daily cap on live calls.
- If Gemini is unavailable, the mandate rules still answer (and say so).

Verdicts: `approve` · `approve_with_conditions` · `ask` · `escalate` · `refuse`. Rating people (appraisals) is always
refused (mandate rule M-R13).

## Blind back-test

Each senior's 15 held-out decisions are replayed as fresh requests: only what the requester wrote, never the answer. The
same pipeline runs twice, rules only and with the Gemini agents. In every pack the last 5 cases are deliberately hard: the
rules see a clean case, but something in the request text matters. One is the reverse: alarming wording on a clean case.

| Senior | Rules alone | Unsafe approvals (rules) | **Pratibimb** | Unsafe approvals | Hard 5 |
|---|---|---|---|---|---|
| Meera (vendors) | 11 / 15 | 4 | **14 / 15** | **0** | 4 / 5 |
| Vikram (leads) | 11 / 15 | 4 | **15 / 15** | **0** | 5 / 5 |
| Kavya (spend) | 11 / 15 | 2 | **15 / 15** | **0** | 5 / 5 |
| **All three** | **33 / 45** | **10** | **44 / 45** | **0** | **14 / 15** |

Scores count ask and escalate as the same call. The one miss (Meera): an urgent fixed-price job approved outright that
Pratibimb approved with a cost cap. Caveat we state openly: the team wrote these cases. Independent cases written by a
practising CA are being added. Per-case output: `backtest_results.json` in each pack folder, and the Back-Test tab.

## Layout

```
pratibimb/
├── agents/
│   ├── llm.py          # one Gemini gateway: Vertex AI auth, cache, cost meter, daily cap, fallback models, trace spans
│   ├── domain.py       # decision packs: personas, generic mandate, documents, request fields per senior
│   ├── store.py        # per-sandbox memory: Cloud Firestore (deployed) or JSON files (local, tests, back-test)
│   ├── mandate.py      # delegation-of-authority rules → the verdict floor
│   ├── precedent.py    # candidate retrieval (holdouts never loaded) + Gemini relevance judgement
│   ├── challenger.py   # Gemini contract review; citations validated against real clauses
│   ├── interviewer.py  # Gemini: Meera's questions
│   ├── decider.py      # Gemini verdict inside the allowed set; rules-only baseline
│   ├── learner.py      # override → lesson + OVR precedent; reset() restores the baseline
│   ├── engine.py       # the ADK Workflow graph; PRATIBIMB_LLM=off runs the same graph on rules only
│   └── backtest.py     # blind back-test, rules vs Gemini → data/backtest_results.json
├── app/main.py         # FastAPI: /api/* plus the built UI on one port
├── data/               # synthetic ground truth (generate_data.py is the source of decisions + back-test)
│   ├── senior.json · mandate.json · vendors.json · contracts.json
│   ├── decisions.json  # 45 decisions: 30 in memory (4 mistakes), 15 held out
│   ├── lessons.json    # L01–L06 (+ any lessons from live overrides); lessons.baseline.json is the reset point
│   ├── requests.json   # 3 demo requests
│   ├── backtest.json   # the 15 held-out cases (request text + Meera's verdict)
│   └── backtest_results.json
├── docs/data-model.md
├── Dockerfile          # UI build + Python runtime, one container
└── ui/                 # React 18 + Vite, Govu design (Aurora / Voltage)
```

## Run locally

```bash
uv sync
cp .env.example .env        # set GOOGLE_CLOUD_PROJECT (Vertex AI) or GEMINI_API_KEY
cd ui && npm install && npm run build && cd ..
uv run uvicorn app.main:app --port 8000     # UI + API on http://localhost:8000
```

```bash
uv run pytest -q                                    # 41 tests, free (rules mode / stubbed Gemini)
uv run python data/validate_data.py                 # data checks
uv run python -m agents.backtest --mode rules       # free: rules-only baseline
uv run python -m agents.backtest --pack all         # rules vs Gemini for all three seniors (~₹8 each; cached reruns free)
uv run python -m agents.llm                         # Gemini spend so far
```

## Container (Cloud Run)

```bash
docker build -t pratibimb .
docker run -p 8080:8080 -e GOOGLE_CLOUD_PROJECT=your-project pratibimb   # cached demo verdicts work without credentials
```

On Cloud Run, Vertex AI auth comes from the service account attached to the service; no keys are baked into the image.
Images are built with Cloud Build into Artifact Registry.

**Firebase Hosting** (`firebase.json`) rewrites every path to the `pratibimb` Cloud Run service, so the site gets a
`web.app` URL and CDN. Hosting forwards only the cookie named `__session`, which is why the visitor sandbox uses that name.

```bash
firebase deploy --only hosting --project pratibimb-aibc
```

## Design

The UI follows the Govu design system: **Aurora** (light: white, blue, orange) and **Voltage** (dark: black, yellow,
green), switched by `<html data-theme>` with a sliding toggle; the choice is remembered, and the first visit follows the
OS setting. Tokens live in `ui/public/govu-tokens.css`; `ui/src/index.css` only adds project classes built from them.

## Tests

`tests/test_pratibimb.py` runs without spending anything. It proves: holdouts never enter memory and back-test requests
carry no answer fields; the mandate floor for 10 request shapes; a stubbed Gemini that answers "approve" with an invented
citation is forced back to "escalate" and loses the fake ID; mandate conditions survive; the daily cap falls back to rules;
an override creates lesson L07 + precedent OVR-001 and reset removes both; the API serves no answers and refuses to re-run
the paid back-test.

## Guardrails

- The mandate floor is deterministic: Gemini can make a verdict stricter, never looser.
- Citations that don't match a real rule, clause, decision or lesson are dropped.
- Holdout decisions are never retrieved; back-test requests carry no answer fields.
- `LLM_DAILY_CALL_CAP` falls back to the rules (and says so) when the day's Gemini budget is used.
