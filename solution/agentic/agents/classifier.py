# agentic/agents/classifier.py
"""
Classifier agent - minimal LLM wrapper interface.
Replace `classify` content with an LLM call returning the same schema.
"""

from typing import Dict, Any

class Classifier:
    # contract: returns dict with intent, domain, requires_knowledge (bool),
    # recommended_tool (list), confidence (0..1)
    def __init__(self, model=None):
        self.model = model

    def classify(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        text = (ticket.get("text") or "").lower()
        intent = "unknown"
        recommended_tool = []
        requires_knowledge = False
        if "refund" in text or "money back" in text or "returned" in text:
            intent = "refund_request"
            recommended_tool = ["refund"]
            requires_knowledge = True
        elif "change address" in text or "update address" in text:
            intent = "account_update"
            recommended_tool = ["account_lookup"]
            requires_knowledge = False
        elif "cancel order" in text or "cancel my order" in text:
            intent = "cancel_order"
            recommended_tool = ["refund","account_lookup"]
            requires_knowledge = True

        confidence = 0.9 if intent != "unknown" else 0.25
        return {
            "intent": intent,
            "domain": "support",
            "requires_knowledge": requires_knowledge,
            "recommended_tool": recommended_tool,
            "confidence": confidence
        }
