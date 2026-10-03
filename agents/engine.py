"""
Pratibimb Agent Engine.
Orchestrates Google ADK multi-agent pipeline:
1. PrecedentAgent (Episodic decision memory)
2. ChallengerAgent (Contract adversarial verification)
3. InterviewerAgent (Instinct interrogatory generation)
4. DeciderAgent (Mandate rule synthesis)
5. LearnerAgent (Feedback ingestion & lesson crystallization)

Outputs the exact frozen verdict JSON contract required by data-model.md.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from agents.models import VendorRequest, VerdictResponse
from agents.precedent import PrecedentAgent
from agents.challenger import ChallengerAgent
from agents.interviewer import InterviewerAgent
from agents.decider import DeciderAgent
from agents.learner import LearnerAgent

try:
    from google.adk.agents.llm_agent import LlmAgent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class PratibimbEngine:
    def __init__(self, data_dir: Path = None, model: str = "gemini-3.8-flash"):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.model_name = model
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Initialize the 5 core agents
        self.precedent_agent = PrecedentAgent(data_dir=self.data_dir)
        self.challenger_agent = ChallengerAgent(data_dir=self.data_dir)
        self.interviewer_agent = InterviewerAgent()
        self.decider_agent = DeciderAgent()
        self.learner_agent = LearnerAgent(data_dir=self.data_dir)

        # Initialize ADK agent wrappers if available
        self.adk_agents = self._init_adk_agents()

    def _init_adk_agents(self) -> Dict[str, Any]:
        """Wrap agents as Google ADK LlmAgent instances for Gemini orchestration."""
        if not ADK_AVAILABLE:
            return {}

        try:
            return {
                "precedent": LlmAgent(
                    name="precedent_agent",
                    instruction="You are the Precedent Agent. Search past decisions and surface lessons from historical outcomes.",
                    model=self.model_name
                ),
                "challenger": LlmAgent(
                    name="challenger_agent",
                    instruction="You are the Challenger Agent. Cross-examine contracts and flag auto-renewals, SLA loopholes, and hidden liabilities.",
                    model=self.model_name
                ),
                "interviewer": LlmAgent(
                    name="interviewer_agent",
                    instruction="You are the Interviewer Agent. Ask the senior's probing questions when parameters are missing or risky.",
                    model=self.model_name
                ),
                "decider": LlmAgent(
                    name="decider_agent",
                    instruction="You are the Decider Agent. Evaluate mandate limits and synthesize audit-ready verdicts with mandatory citations.",
                    model=self.model_name
                ),
                "learner": LlmAgent(
                    name="learner_agent",
                    instruction="You are the Learner Agent. Crystallize senior overrides into permanent governance lessons.",
                    model=self.model_name
                )
            }
        except Exception:
            return {}

    def decide(self, request_data: Dict[str, Any]) -> VerdictResponse:
        """
        Execute multi-agent deliberation on an incoming vendor request.
        Returns frozen VerdictResponse schema.
        """
        req = VendorRequest(**request_data)

        # 1. Precedent Agent retrieves similar decisions & applicable lessons
        precedents, cited_lessons = self.precedent_agent.retrieve(req)

        # 2. Challenger Agent cross-examines contract clauses & vendor flags
        challenges, clause_citations = self.challenger_agent.challenge(req)

        # 3. Interviewer Agent formulates instinct questions
        questions = self.interviewer_agent.formulate_questions(req, challenges)

        # 4. Decider Agent applies mandate rules and synthesizes verdict
        verdict = self.decider_agent.evaluate(
            req=req,
            precedents=precedents,
            challenges=challenges,
            questions=questions,
            cited_lessons=cited_lessons,
            clause_citations=clause_citations
        )

        return verdict

    def evaluate_live_requests(self) -> Dict[str, Any]:
        """Runs the 3 canonical live demo requests (PrintPro, Kestrel, Parlo)."""
        req_path = self.data_dir / "requests.json"
        with open(req_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = []
        for r in data.get("requests", []):
            verdict = self.decide(r)
            results.append({
                "request_id": r["id"],
                "vendor_name": r.get("vendor_name"),
                "expected_verdict": r.get("expected_verdict"),
                "actual_verdict": verdict.verdict,
                "headline": verdict.headline,
                "citations": verdict.citations,
                "matches_expected": (verdict.verdict == r.get("expected_verdict"))
            })
        return {"live_demo_results": results}
