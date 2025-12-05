# agentic/node_utils.py
import traceback
from typing import Callable, Any, Dict
from functools import wraps

def safe_node(node_fn: Callable):
    """
    Wrap a LangGraph node function so:
     - Exceptions are caught
     - An audit event is added to state['audit']
     - state['error'] is set and supervisor decision is set to escalation
     - Node returns state so graph continues to finalization (graceful handling)
    """
    @wraps(node_fn)
    def wrapper(state: Dict[str, Any]):
        try:
            return node_fn(state)
        except Exception as exc:
            # record the error in audit
            audit = state.setdefault("audit", {"id": f"error_{state.get('ticket',{}).get('ticket_id','unknown')}", "events": []})
            err_payload = {
                "error": str(exc),
                "traceback": traceback.format_exc()
            }
            # append event
            audit.setdefault("events", []).append({"ts": __import__("datetime").datetime.utcnow().isoformat(), "type": "node_error", "payload": err_payload})
            # place error marker in state
            state["error"] = {"node": node_fn.__name__, "error": str(exc)}
            # mark supervisor decision as escalate (so later router picks escalation path)
            state["supervisor_decision"] = {"escalate": True, "reason": "node_error", "node": node_fn.__name__}
            # return state to allow graph to proceed to finalize (or escalation)
            return state
    return wrapper
