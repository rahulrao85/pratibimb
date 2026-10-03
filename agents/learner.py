"""
Learner Agent for Pratibimb.
Ingests senior overrides and post-decision operational outcomes, generating
versioned governance lessons to continuously refine the decision engine.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class LearnerAgent:
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir

    def record_override(
        self,
        request_id: str,
        engine_verdict: str,
        senior_decision: str,
        senior_override_note: str,
        proposed_rule: str,
        senior_name: str = "Meera Nair",
    ) -> Dict[str, Any]:
        lessons_path = self.data_dir / "lessons.json"
        with open(lessons_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_lessons = data.get("lessons", [])
        next_num = len(existing_lessons) + 1
        new_id = f"L{next_num:02d}"

        new_lesson = {
            "id": new_id,
            "version": 1,
            "status": "approved",
            "title": f"Governance Rule from Override ({request_id})",
            "rule": proposed_rule,
            "trigger": f"Derived from override on request {request_id}",
            "action_required": senior_override_note,
            "source_decision_ids": [request_id],
            "created": "2026-10-04",
            "approved_by": senior_name,
            "half_life_days": 540
        }

        existing_lessons.append(new_lesson)
        data["lessons"] = existing_lessons

        with open(lessons_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return new_lesson
