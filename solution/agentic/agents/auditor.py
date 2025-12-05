# agentic/auditor.py
import json
import os
from datetime import datetime
from typing import Dict, Any, Iterable, List, Optional

AUDIT_DIR = os.environ.get("AUDIT_DIR", "./data/core/audit")
AUDIT_FILE = os.path.join(AUDIT_DIR, "audit.jsonl")

def ensure_audit_dir():
    os.makedirs(AUDIT_DIR, exist_ok=True)

class Auditor:
    def __init__(self, audit_file: str = AUDIT_FILE):
        ensure_audit_dir()
        self.audit_file = audit_file

    def new_audit(self, ticket_id: str) -> Dict[str, Any]:
        return {
            "id": f"audit_{ticket_id}_{datetime.utcnow().isoformat()}",
            "ticket_id": ticket_id,
            "created_at": datetime.utcnow().isoformat(),
            "events": []
        }

    def add_event(self, audit: Dict[str, Any], event_type: str, payload: Dict[str, Any]):
        evt = {
            "ts": datetime.utcnow().isoformat(),
            "type": event_type,
            "payload": payload
        }
        # ensure events list exists
        audit.setdefault("events", []).append(evt)

    def persist(self, audit: Dict[str, Any]):
        # write audit to JSONL
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit, default=str) + "\n")

    # Simple load all audits (generator)
    def iter_audits(self) -> Iterable[Dict[str, Any]]:
        if not os.path.exists(self.audit_file):
            return []
        with open(self.audit_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    # Search audits with simple filters (ticket_id, event_type, key/value in payload)
    def search_audits(self, ticket_id: Optional[str]=None, event_type: Optional[str]=None, contains: Optional[str]=None, limit: int = 100) -> List[Dict[str, Any]]:
        results = []
        for audit in self.iter_audits():
            if ticket_id and audit.get("ticket_id") != ticket_id:
                continue
            if not event_type and not contains:
                results.append(audit)
            else:
                # filter by events
                for e in audit.get("events", []):
                    if event_type and e.get("type") != event_type:
                        continue
                    if contains:
                        # search in payload json string
                        try:
                            payload_str = json.dumps(e.get("payload", {}))
                        except Exception:
                            payload_str = str(e.get("payload", ""))
                        if contains not in payload_str:
                            continue
                    results.append(audit)
                    break
            if len(results) >= limit:
                break
        return results
