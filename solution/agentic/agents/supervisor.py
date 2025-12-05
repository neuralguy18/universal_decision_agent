# agentic/agents/supervisor.py
from typing import Dict, Any

class Supervisor:
    """
    Supervisor uses classifier + resolver outputs + policy to decide:
      - retrieve (bool)
      - auto_resolve (bool)
      - escalate (bool)
    """
    def __init__(self, auto_threshold: float = 0.75, safe_threshold: float = 0.5):
        self.auto_threshold = auto_threshold
        self.safe_threshold = safe_threshold

    def decide(self, classifier_out: Dict[str, Any], resolver_out: Dict[str, Any], ticket: Dict[str, Any]) -> Dict[str, Any]:
        c = classifier_out.get("confidence", 0.0)
        r = resolver_out.get("confidence", 0.0)
        composite = 0.6 * c + 0.4 * r
        reason = f"composite={composite:.3f} (c={c}, r={r})"
        # urgency/safety overrides
        urgency = ticket.get("metadata", {}).get("urgency", "medium")
        destructive_actions = any(a.get("tool") in ["refund", "account_lookup"] for a in resolver_out.get("actions", []))
        if urgency == "high" and destructive_actions:
            return {"retrieve": True, "auto_resolve": False, "escalate": True, "reason": "high urgency + destructive action"}
        if composite >= self.auto_threshold:
            return {"retrieve": classifier_out.get("requires_knowledge", False), "auto_resolve": True, "escalate": False, "reason": reason}
        if composite >= self.safe_threshold:
            return {"retrieve": classifier_out.get("requires_knowledge", False), "auto_resolve": False, "escalate": False, "reason": reason + " (safe resolution, QA required)"}
        return {"retrieve": True, "auto_resolve": False, "escalate": True, "reason": reason + " (low confidence)"}
