# agentic/tools/refund.py
from typing import Dict, Any
from ..tools.tools_utils import now_iso

REFUND_CAP = 5000.0

def validate_params(params: Dict[str, Any]) -> Dict[str, Any]:
    required = ["user_id","order_id","amount"]
    missing = [p for p in required if p not in params or params[p] is None]
    if missing:
        return {"ok": False, "error": f"missing_params: {missing}"}
    try:
        amount = float(params["amount"])
    except Exception:
        return {"ok": False, "error": "invalid_amount"}
    if amount > REFUND_CAP:
        return {"ok": False, "error": "amount_above_limit", "allowed_max": REFUND_CAP}
    return {"ok": True}

def call(params: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    v = validate_params(params)
    if not v["ok"]:
        return {"success": False, "error": v.get("error")}
    if dry_run:
        return {"success": True, "dry_run": True, "sim_tx": {"tx_id": f"sim-{params['order_id']}", "amount": params["amount"], "ts": now_iso()}}
    # Replace with real API call to payment/refund service
    tx = {"tx_id": f"tx-{params['order_id']}", "amount": params["amount"], "processed_at": now_iso()}
    return {"success": True, "dry_run": False, "result": tx}
