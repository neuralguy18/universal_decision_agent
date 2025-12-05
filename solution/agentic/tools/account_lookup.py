# agentic/tools/account_lookup.py
from typing import Dict, Any
from ..tools.tools_utils import now_iso

FAKE_DB = {
    "user_abc": {"email":"alice@example.com", "address":"Old Address 12", "orders":["ORDER123","ORDER456"] }
}

def get_account(user_id: str) -> Dict[str, Any]:
    return FAKE_DB.get(user_id, {})

def update_account(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    acct = FAKE_DB.get(user_id)
    if not acct:
        return {"success": False, "error": "user_not_found"}
    acct.update(updates)
    acct["updated_at"] = now_iso()
    return {"success": True, "account": acct}
