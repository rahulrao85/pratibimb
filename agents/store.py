"""
Where Pratibimb keeps what it learns.

The senior's baseline memory (decisions.json, lessons.json) is read-only, part of the repo. What she teaches it later
(lessons from overrides, and her overridden decisions filed as precedents) lives in a Store, per sandbox: every
visitor of the live demo gets their own sandbox, so a judge's overrides never leak into anyone else's demo, and they
survive restarts and new deployments.

  FirestoreStore — Cloud Firestore (PRATIBIMB_STORE=firestore; used on Cloud Run)
  FileStore      — JSON files on disk (local development, tests, the back-test)

Layout in Firestore:
  sandboxes/{sid}/lessons/{L07…}      lessons Meera taught in this sandbox
  sandboxes/{sid}/overrides/{OVR-…}   her overridden decisions, as precedents
  verdicts/{auto-id}                  append-only log of every verdict (sid, request, verdict, engine, cost, time)
"""
import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List

SID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def clean_sid(sid: str) -> str:
    return sid if sid and SID_PATTERN.match(sid) else "local"


class FileStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self._lock = threading.Lock()

    def _path(self, sid: str) -> Path:
        return self.root / "sandboxes" / f"{clean_sid(sid)}.json"

    def _read(self, sid: str) -> Dict[str, List[Dict[str, Any]]]:
        p = self._path(sid)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"lessons": [], "overrides": []}

    def _write(self, sid: str, data: Dict[str, Any]) -> None:
        p = self._path(sid)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def lessons(self, sid: str) -> List[Dict[str, Any]]:
        return self._read(sid)["lessons"]

    def overrides(self, sid: str) -> List[Dict[str, Any]]:
        return self._read(sid)["overrides"]

    def add_lesson(self, sid: str, lesson: Dict[str, Any]) -> None:
        with self._lock:
            d = self._read(sid)
            d["lessons"].append(lesson)
            self._write(sid, d)

    def add_override(self, sid: str, rec: Dict[str, Any]) -> None:
        with self._lock:
            d = self._read(sid)
            d["overrides"].append(rec)
            self._write(sid, d)

    def reset(self, sid: str) -> None:
        with self._lock:
            p = self._path(sid)
            if p.exists():
                p.unlink()

    def log_verdict(self, sid: str, record: Dict[str, Any]) -> None:
        with self._lock:
            self.root.mkdir(parents=True, exist_ok=True)
            with open(self.root / "verdicts.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sid": clean_sid(sid), **record}, ensure_ascii=False) + "\n")

    @property
    def kind(self) -> str:
        return "file"


class FirestoreStore:
    def __init__(self, project: str = None, database: str = "(default)"):
        from google.cloud import firestore

        from agents import llm

        self._fs = firestore
        self.db = firestore.Client(project=project or llm.PROJECT, credentials=llm.credentials(), database=database)

    def _box(self, sid: str):
        return self.db.collection("sandboxes").document(clean_sid(sid))

    @staticmethod
    def _sorted(docs, key: str) -> List[Dict[str, Any]]:
        return sorted((d.to_dict() for d in docs), key=lambda x: x.get(key, ""))

    def lessons(self, sid: str) -> List[Dict[str, Any]]:
        return self._sorted(self._box(sid).collection("lessons").stream(), "seq")

    def overrides(self, sid: str) -> List[Dict[str, Any]]:
        return self._sorted(self._box(sid).collection("overrides").stream(), "seq")

    def add_lesson(self, sid: str, lesson: Dict[str, Any]) -> None:
        box = self._box(sid)
        box.set({"updated": self._fs.SERVER_TIMESTAMP}, merge=True)
        box.collection("lessons").document(lesson["id"]).set({**lesson, "seq": lesson["id"]})

    def add_override(self, sid: str, rec: Dict[str, Any]) -> None:
        box = self._box(sid)
        box.set({"updated": self._fs.SERVER_TIMESTAMP}, merge=True)
        box.collection("overrides").document(rec["id"]).set({**rec, "seq": rec["id"]})

    def reset(self, sid: str) -> None:
        box = self._box(sid)
        for sub in ("lessons", "overrides"):
            for d in box.collection(sub).stream():
                d.reference.delete()
        box.delete()

    def log_verdict(self, sid: str, record: Dict[str, Any]) -> None:
        self.db.collection("verdicts").add({"sid": clean_sid(sid), "ts": self._fs.SERVER_TIMESTAMP, **record})

    @property
    def kind(self) -> str:
        return "firestore"


def make_store(default_root: Path):
    if os.getenv("PRATIBIMB_STORE", "file").lower() == "firestore":
        return FirestoreStore()
    return FileStore(default_root)
