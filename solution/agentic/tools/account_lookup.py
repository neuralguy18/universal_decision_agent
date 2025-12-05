from sqlalchemy.orm import Session
from models import User, Account  # your earlier ORM models

class AccountLookupTool:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    def call(self, user_id: str):
        """Look up account info from real database."""
        with self.db_session_factory() as session:
            user = session.query(User).filter_by(user_id=user_id).first()

            if not user:
                return {
                    "status": "error",
                    "message": f"User with ID {user_id} not found."
                }

            account = session.query(Account).filter_by(user_id=user_id).first()

            if not account:
                return {
                    "status": "error",
                    "message": f"Account record missing for user {user_id}."
                }

            return {
                "status": "success",
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "balance": account.balance,
                "membership": account.membership_type,
                "updated_at": account.updated_at.isoformat()
            }
