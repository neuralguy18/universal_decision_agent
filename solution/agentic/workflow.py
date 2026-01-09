# agentic/workflow.py
"""
LangGraph-based workflow for the Universal Decision Agent (updated with Option A memory changes and correct LLM usage).
- Preserves all original nodes and graph structure.
- Adds TicketMessage persistence, reads ticket messages for session/user, and stores resolved issues in LTM metadata.
- Minimal additions only; no destructive edits.
- Resolver initialized with LLM to fix __init__ error.
"""

from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .agents import Classifier, Retriever, Resolver, Supervisor, Escalation, Auditor
from .memory.memory_repo import MemoryRepository
from .tools import refund as refund_tool
from utils import new_id, now_iso
from .node_utils import safe_node
import os
from dotenv import load_dotenv

# Import LLM
from langchain_openai import ChatOpenAI

load_dotenv()

# ---------------------------------------------------------------------
# 1. DEFINE STATE SCHEMA
# ---------------------------------------------------------------------
class WorkflowState(TypedDict, total=False):
    ticket: Dict[str, Any]
    session_id: Optional[str]
    stm_context: Optional[List[Dict[str, Any]]]
    ticket_messages: Optional[List[Dict[str, Any]]]   # historic messages loaded
    ltm_docs: Optional[List[Dict[str, Any]]]
    classifier_output: Optional[Dict[str, Any]]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    resolver_output: Optional[Dict[str, Any]]
    supervisor_decision: Optional[Dict[str, Any]]
    tool_results: Optional[List[Dict[str, Any]]]
    audit: Optional[Dict[str, Any]]


# ---------------------------------------------------------------------
# 2. INITIALIZE AGENTS & MEMORY (with LLM for Resolver)
# ---------------------------------------------------------------------
# --- LLM import & initialization: version-safe ---
llm = ChatOpenAI(
    model_name=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
    temperature=float(os.environ.get("LLM_TEMP", 0))
)

resolver = Resolver(llm=llm)

if resolver.llm is None:
    print("⚠️ Warning: Resolver LLM is not initialized!")
else:
    print("✅ Resolver LLM is initialized correctly")


supervisor = Supervisor(auto_threshold=float(os.environ.get("DEFAULT_CONFIDENCE_THRESHOLD", 0.75)))
escalation_agent = Escalation()
auditor = Auditor()
memory_repo = MemoryRepository()


# ---------------------------------------------------------------------
# 3. NODE FUNCTIONS
# ---------------------------------------------------------------------
def node_load_stm(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    session_id = state.get("session_id") or ticket.get("metadata", {}).get("thread_id")
    if not session_id:
        session_id = f"session_{ticket.get('ticket_id', new_id())}"
    state["session_id"] = session_id

    # Load STM
    try:
        stm_rows = memory_repo.get_short(session_id=session_id)
        stm_context = []
        for row in stm_rows or []:
            if hasattr(row, "payload_json"):
                stm_context.append(row.payload_json)
            elif isinstance(row, dict):
                stm_context.append(row)
            else:
                stm_context.append(getattr(row, "__dict__", {}))
        state["stm_context"] = stm_context
    except Exception as e:
        state["stm_context"] = []
        auditor.add_event(state.setdefault("audit", auditor.new_audit(ticket.get("ticket_id", "unknown"))),
                         "load_stm_error", {"error": str(e)})

    # Load ticket messages
    try:
        messages = memory_repo.get_ticket_messages(session_id=session_id, limit=50)
        if not messages and ticket.get("user_id"):
            messages = memory_repo.get_ticket_messages(user_id=ticket.get("user_id"), limit=50)
        state["ticket_messages"] = messages or []
        auditor.add_event(state["audit"], "load_ticket_messages", {"count": len(messages or [])})
    except Exception as e:
        state["ticket_messages"] = []
        auditor.add_event(state["audit"], "load_ticket_messages_error", {"error": str(e)})

    return state


def node_ingest(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    audit = state.get("audit") or auditor.new_audit(ticket.get("ticket_id", new_id()))
    state["audit"] = audit
    auditor.add_event(audit, "ingest", {"ticket_id": ticket.get("ticket_id")})
    return state


def node_classifier(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    c_out = classifier.classify(ticket)
    auditor.add_event(state["audit"], "classifier", c_out)
    state["classifier_output"] = c_out
    return state


def node_ltm_retrieve(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    text = ticket.get("text", "")
    ltm_docs = []
    if text:
        try:
            hits = memory_repo.semantic_search(text, top_k=5)
            for h in hits:
                if isinstance(h, tuple) and len(h) == 2:
                    row, score = h
                    item = {
                        "id": getattr(row, "id", None),
                        "text": getattr(row, "text", None),
                        "score": float(score),
                        "metadata": getattr(row, "metadata_json", None),
                    }
                else:
                    item = {
                        "id": getattr(h, "id", None),
                        "text": getattr(h, "text", None),
                        "score": getattr(h, "score", None),
                        "metadata": getattr(h, "metadata_json", None),
                    }
                ltm_docs.append(item)
            auditor.add_event(state["audit"], "ltm_retrieve", {"count": len(ltm_docs)})
        except Exception as e:
            auditor.add_event(state["audit"], "ltm_retrieve_error", {"error": str(e)})
    state["ltm_docs"] = ltm_docs
    return state


def node_retriever(state: WorkflowState) -> WorkflowState:
    c_out = state.get("classifier_output", {})
    requires = c_out.get("requires_knowledge", False)
    docs = retriever.retrieve(state["ticket"]) if requires else []

    # Merge LTM
    merged = []
    ids = set()
    for d in docs:
        merged.append({**d, "source": d.get("source", "kb")})
        if d.get("id"):
            ids.add(d.get("id"))
    for l in state.get("ltm_docs", []) or []:
        if l.get("id") not in ids:
            merged.append({**l, "source": "ltm"})
    state["retrieved_docs"] = merged
    auditor.add_event(state["audit"], "retriever", {"count": len(merged)})
    return state


def node_resolver(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    context_docs = state.get("retrieved_docs", []) or []
    stm_context = state.get("stm_context", []) or []
    ticket_messages = state.get("ticket_messages", []) or []
    allowed_tools = state.get("classifier_output", {}).get("recommended_tool")

    r_out = resolver.resolve(
        ticket,
        context_docs=context_docs,
        allowed_tools=allowed_tools,
        stm_context=stm_context,
        ticket_messages=ticket_messages,
        ltm_docs=state.get("ltm_docs", []),
    )
    auditor.add_event(state["audit"], "resolver", r_out)
    state["resolver_output"] = r_out
    return state


def node_supervisor(state: WorkflowState) -> WorkflowState:
    decision = supervisor.decide(
        state.get("classifier_output", {}),
        state.get("resolver_output", {}),
        state.get("ticket", {}),
        stm_context=state.get("stm_context", []),
        ticket_messages=state.get("ticket_messages", []),
        ltm_context=state.get("ltm_docs", []),
    )
    auditor.add_event(state["audit"], "supervisor", decision)
    state["supervisor_decision"] = decision
    return state


def node_tools(state: WorkflowState) -> WorkflowState:
    r_out = state.get("resolver_output", {})
    ticket = state.get("ticket", {})
    results = []
    for action in r_out.get("actions", []) if r_out else []:
        tool_name = action.get("tool")
        params = action.get("params", {}) or {}
        if not params.get("user_id") and ticket.get("user_id"):
            params["user_id"] = ticket.get("user_id")

        if tool_name == "refund":
            res = refund_tool.call(params, dry_run=True)
            auditor.add_event(state["audit"], "tool_call", {"tool": "refund", "params": params, "result": res})
            results.append({"tool": "refund", "params": params, "result": res})
        else:
            auditor.add_event(state["audit"], "tool_call", {"tool": tool_name, "params": params, "result": "tool_not_implemented"})
            results.append({"tool": tool_name, "params": params, "result": "tool_not_implemented"})

    state["tool_results"] = results
    return state


def node_escalation(state: WorkflowState) -> WorkflowState:
    esc = escalation_agent.package(
        state.get("ticket", {}),
        state.get("classifier_output", {}),
        state.get("resolver_output", {}),
        context_docs=state.get("retrieved_docs", []),
        audit_events=state.get("audit", {}).get("events", []),
    )
    auditor.add_event(state["audit"], "escalation", esc)
    return state


def node_finalize(state: WorkflowState) -> WorkflowState:
    ticket = state.get("ticket", {})
    session_id = ticket.get("metadata", {}).get("thread_id") or f"session_{ticket.get('ticket_id', new_id())}"
    ticket_id = ticket.get("ticket_id")

    # STM
    try:
        memory_repo.put_short(
            session_id=session_id,
            ticket_id=ticket_id,
            payload={
                "ticket": ticket,
                "classifier": state.get("classifier_output"),
                "resolver": state.get("resolver_output"),
                "decision": state.get("supervisor_decision"),
            },
        )
        auditor.add_event(state["audit"], "stm_store", {"session_id": session_id})
    except Exception as e:
        auditor.add_event(state["audit"], "stm_store_error", {"error": str(e)})

    # Ticket messages
    try:
        user_text = ticket.get("text", "")
        if user_text:
            memory_repo.put_ticket_message(session_id=session_id, ticket_id=ticket_id, from_role="user",
                                           text=user_text, metadata={"created_at": ticket.get("created_at")})
            auditor.add_event(state["audit"], "ticket_message_stored", {"role": "user"})

        resolver_out = state.get("resolver_output", {}) or {}
        agent_text = resolver_out.get("response") or resolver_out.get("message") or None
        if agent_text:
            memory_repo.put_ticket_message(session_id=session_id, ticket_id=ticket_id, from_role="agent",
                                           text=agent_text,
                                           metadata={"resolved": bool(state.get("supervisor_decision", {}).get("auto_resolve", False))})
            auditor.add_event(state["audit"], "ticket_message_stored", {"role": "agent"})
    except Exception as e:
        auditor.add_event(state["audit"], "ticket_message_store_error", {"error": str(e)})

    # LTM
    try:
        decision = state.get("supervisor_decision", {}) or {}
        resolver_out = state.get("resolver_output", {}) or {}
        if decision.get("auto_resolve") and (resolver_out.get("response") or resolver_out.get("message")):
            resolved_text = resolver_out.get("response") or resolver_out.get("message")
            memory_repo.put_long(
                user_id=ticket.get("user_id"),
                ticket_id=ticket_id,
                text=f"Resolved: {resolved_text}",
                embedding=None,
                metadata={
                    "resolved": True,
                    "intent": (state.get("classifier_output") or {}).get("intent"),
                    "created_at": now_iso(),
                }
            )
            auditor.add_event(state["audit"], "ltm_stored", {"summary": resolved_text[:200]})
    except Exception as e:
        auditor.add_event(state["audit"], "ltm_store_error", {"error": str(e)})

    try:
        auditor.persist(state["audit"])
    except Exception:
        pass

    return state


# ---------------------------------------------------------------------
# 4. BUILD LANGGRAPH STATEGRAPH
# ---------------------------------------------------------------------
graph = StateGraph(WorkflowState)
graph.add_node("load_stm", safe_node(node_load_stm))
graph.add_node("ingest", safe_node(node_ingest))
graph.add_node("classifier", safe_node(node_classifier))
graph.add_node("ltm_retrieve", safe_node(node_ltm_retrieve))
graph.add_node("retriever", safe_node(node_retriever))
graph.add_node("resolver", safe_node(node_resolver))
graph.add_node("supervisor", safe_node(node_supervisor))
graph.add_node("tools", safe_node(node_tools))
graph.add_node("escalation", safe_node(node_escalation))
graph.add_node("finalize", safe_node(node_finalize))

graph.set_entry_point("load_stm")
graph.add_edge("load_stm", "ingest")
graph.add_edge("ingest", "classifier")
graph.add_edge("classifier", "ltm_retrieve")
graph.add_edge("ltm_retrieve", "retriever")
graph.add_edge("retriever", "resolver")
graph.add_edge("resolver", "supervisor")

def supervisor_router(state: WorkflowState):
    decision = state.get("supervisor_decision", {}) or {}
    if decision.get("auto_resolve"):
        return "tools"
    elif decision.get("escalate"):
        return "escalation"
    else:
        return "finalize"

graph.add_conditional_edges("supervisor", supervisor_router)
graph.add_edge("tools", "finalize")
graph.add_edge("escalation", "finalize")

workflow = graph.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------
# 5. PUBLIC RUN FUNCTION
# ---------------------------------------------------------------------
def orchestrator(ticket: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    initial_state: WorkflowState = {"ticket": ticket}

    if session_id:
        initial_state["session_id"] = session_id

    result_state = workflow.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": session_id
            }
        }
    )

    return {
        "ticket": ticket,
        "classifier": result_state.get("classifier_output"),
        "resolver": result_state.get("resolver_output"),
        "decision": result_state.get("supervisor_decision"),
        "tool_results": result_state.get("tool_results", []),
        "audit": result_state.get("audit"),
        "stm_context": result_state.get("stm_context", []),
        "ticket_messages": result_state.get("ticket_messages", []),
        "ltm_docs": result_state.get("ltm_docs", []),
    }


# optional quick demo
if __name__ == "__main__":
    t = {
        "ticket_id": new_id(),
        "platform": "email",
        "user_id": "user_abc",
        "text": "I want a refund for my order 12345. I never received it.",
        "metadata": {"urgency": "medium", "language": "en", "thread_id": "thread_1"},
        "attachments": [],
        "created_at": now_iso()
    }
    out = orchestrator(t, session_id="thread_1")
    import json
    print(json.dumps(out["audit"], indent=2))
