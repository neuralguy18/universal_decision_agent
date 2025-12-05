# agentic/agents/auditor.py
import json
from typing import Dict, Any, List
from utils import now_iso, ensure_dir, save_json
import os

class Auditor:
    def __init__(self, out_dir: str = None):
        self.out_dir = out_dir or os.path.join(os.getcwd(), "data", "core")
        ensure_dir(self.out_dir)

    def new_audit(self, ticket_id: str) -> Dict[str, Any]:
        return {"ticket_id": ticket_id, "events": [], "created_at": now_iso()}

    def add_event(self, audit: Dict[str, Any], step: str, output: Any):
        audit["events"].append({"ts": now_iso(), "step": step, "output": output})
        return audit

    def persist(self, audit: Dict[str, Any]):
        path = os.path.join(self.out_dir, f"audit_{audit['ticket_id']}.json")
        save_json(path, audit)
