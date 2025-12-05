# agentic/workflow.py
"""
Custom graph orchestrator (no prebuilt workflow used).
The orchestrator builds a small DAG and executes nodes sequentially.
Save this file as agentic/workflow.py (replace the sample).
"""

from typing import Dict, Any
from .agents import Classifier, Retriever, Resolver, Supervisor, Escalation, Auditor
from .memory.memory_repo import MemoryRepository
from .tools import refund as refund_tool
from .embeddings import embedding_fn
from utils import new_id, now_iso
from dotenv import load_dotenv
import os

load_dotenv()

# initialize components
memory_repo = MemoryRepository(db_url=os.environ.get("MEMORY_DB_URL"))
classifier = Classifier()
retriever = Retriever(memory_repo=memory_repo)
resolver = Resolver()
supervisor = Supervisor(auto_threshold=float(os.environ.get("DEFAULT_CONFIDENCE_THRESHOLD", 0.75)))
escalation_agent = Escalation()
auditor = Auditor()

# Graph function: ingest -> classify -> decide(retrieve?) -> retrieve -> resolve -> supervisor decide -> execute tool or escalate -> audit
def orchestrator(ticket: Dict[str, Any], session_id: str = None, dry_run: bool = True) -> Dict[str, Any]:
    session_id = session_id or ticket.get("metadata", {}).get("thread_id") or f"session_{ticket['ticket_id']}"
    audit = auditor.new_audit(ticket["ticket_id"])

    # Node: classify
    c_out = classifier.classify(ticket)
    auditor.add_event(audit, "classify", c_out)

    # Minimal Supervisor pre-check (we'll call again after resolver)
    # Node: decide whether to retrieve (early check)
    requires_rag = c_out.get("requires_knowledge", False)
    if requires_rag:
        auditor.add_event(audit, "decision_pre", {"retrieve": True})
    else:
        auditor.add_event(audit, "decision_pre", {"retrieve": False})

    # Node: retriever (if requested by classifier or later by supervisor)
    context_docs = retriever.retrieve(ticket) if requires_rag else []
    auditor.add_event(audit, "retrieve", {"count": len(context_docs), "docs": [d.get("id") for d in context_docs]})

    # Node: resolver
    r_out = resolver.resolve(ticket, context_docs=context_docs, allowed_tools=c_out.get("recommended_tool"))
    auditor.add_event(audit, "resolve", r_out)

    # Node: Supervisor final decision
    decision = supervisor.decide(c_out, r_out, ticket)
    auditor.add_event(audit, "supervisor", decision)

    # Node: If auto_resolve -> execute actions (tools) with safety checks
    tool_results = []
    if decision.get("auto_resolve"):
        for action in r_out.get("actions", []):
            tool_name = action.get("tool")
            params = action.get("params", {})
            # minimal param fill logic: try to pull order_id from ticket text
            if not params.get("order_id") and "order" in ticket.get("text","").lower():
                # naive extraction: last token numeric
                toks = [t.strip(".,") for t in ticket["text"].split()]
                for t in toks[::-1]:
                    if t.isdigit():
                        params["order_id"] = t
                        break
            if not params.get("amount") and "amount" in params:
                params["amount"] = params.get("amount", None)
            # route to tool
            if tool_name == "refund":
                res = refund_tool.call(params, dry_run=dry_run)
                tool_results.append({"tool":"refund","params":params,"result":res})
                auditor.add_event(audit, "tool_call", {"tool":"refund","params":params,"result":res})
            else:
                auditor.add_event(audit, "tool_call", {"tool": tool_name, "params": params, "result": "tool_not_found"})
    else:
        if decision.get("escalate"):
            esc = escalation_agent.package(ticket, c_out, r_out, context_docs=context_docs, audit_events=audit["events"])
            auditor.add_event(audit, "escalation", {"payload": esc})
        else:
            auditor.add_event(audit, "manual_review", {"reason": "safe_resolve_path"})

    # store short-term memory: session/thread context
    memory_repo.put_short(session_id=session_id, ticket_id=ticket["ticket_id"], payload={"classifier": c_out, "resolver": r_out, "decision": decision})

    # optionally store long-term memory if auto_resolve and user_consent (not implemented here)
    auditor.persist(audit)

    return {"ticket": ticket, "classifier": c_out, "resolver": r_out, "decision": decision, "tool_results": tool_results, "audit": audit}

# quick demo main
if __name__ == "__main__":
    t = {
        "ticket_id": new_id("t"),
        "platform": "email",
        "user_id": "user_abc",
        "text": "I want a refund for my order 12345. I never received it.",
        "metadata": {"urgency":"medium", "language":"en", "thread_id": "thread_1"},
        "attachments": [],
        "created_at": now_iso()
    }
    out = run_ticket(t, session_id="thread_1", dry_run=True)
    import json
    print(json.dumps(out["audit"], indent=2))
