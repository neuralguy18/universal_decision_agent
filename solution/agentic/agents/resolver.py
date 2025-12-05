# agentic/agents/resolver.py
from typing import Dict, Any, List

class Resolver:
    """
    Resolver contract:
      resolve(ticket, context_docs, allowed_tools) -> dict with:
        response_text, actions(list), confidence, explanation
    Replace the body with real LLM invocation and schema validation.
    """
    def __init__(self, model=None):
        self.model = model

    def resolve(self, ticket: Dict[str, Any], context_docs: List[Dict[str, Any]] = None, allowed_tools=None) -> Dict[str, Any]:
        text = ticket.get("text","").lower()
        context_docs = context_docs or []
        if "refund" in text:
            response_text = "We can process a refund. Please confirm your order id and the amount to proceed."
            actions = [{"tool":"refund","params":{"user_id": ticket["user_id"], "order_id": None, "amount": None}}]
            confidence = 0.8
        elif "address" in text:
            response_text = "We can update your address. Please confirm the new address and last 4 digits of payment method."
            actions = [{"tool":"account_lookup","params":{"user_id": ticket["user_id"], "update_fields": {"address": None}}}]
            confidence = 0.75
        else:
            response_text = "Thanks for contacting support. Could you clarify your request so we can help?"
            actions = []
            confidence = 0.35
        return {"response_text": response_text, "actions": actions, "confidence": confidence, "explanation": "rule-based resolver"}
