# agentic/agents/escalation.py
from typing import Dict, Any, List

class Escalation:
    def package(self, ticket: Dict[str, Any], classifier_out: Dict[str, Any], resolver_out: Dict[str, Any], context_docs: List[Dict[str, Any]], audit_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        md = []
        md.append(f"### Escalation — Ticket {ticket.get('ticket_id')}")
        md.append(f"- **User**: {ticket.get('user_id')}")
        md.append(f"- **Intent**: {classifier_out.get('intent')}, confidence {classifier_out.get('confidence')}")
        md.append(f"- **Resolver confidence**: {resolver_out.get('confidence')}")
        md.append(f"- **Reason**: {resolver_out.get('explanation')}")
        md.append("\n**Retrieved docs**:")
        for d in context_docs or []:
            md.append(f"- {d.get('source')} `{d.get('id')}` (score={d.get('score')})")
        md.append("\n**Audit events**:")
        for e in audit_events[-5:]:
            md.append(f"- {e.get('step')}: {e.get('output', e.get('reason', ''))}")
        return {"escalation_md": "\n".join(md), "ticket_id": ticket.get("ticket_id")}
