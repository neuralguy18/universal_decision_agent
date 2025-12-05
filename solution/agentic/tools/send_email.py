# agentic/tools/send_email.py
from typing import Dict, Any
from ..tools.tools_utils import now_iso

def send_email(to: str, subject: str, body: str, dry_run: bool = True) -> Dict[str, Any]:
    if dry_run:
        return {"success": True, "dry_run": True, "preview": {"to": to, "subject": subject, "body": body[:400], "ts": now_iso()}}
    # integrate with SMTP or SendGrid here
    return {"success": True, "message_id": f"msg-{now_iso()}"}
