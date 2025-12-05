class RefundTool:
    def __init__(self, db_session_factory, refund_cap=5000):
        self.db_session_factory = db_session_factory
        self.refund_cap = refund_cap

    def call(self, user_id: str, amount: float):
        if amount <= 0:
            return {"status": "error", "message": "Refund amount must be greater than zero."}

        if amount > self.refund_cap:
            return {
                "status": "error",
                "message": f"Refund amount exceeds cap of ₹{self.refund_cap}."
            }

        with self.db_session_factory() as session:
            account = session.query(Account).filter_by(user_id=user_id).first()

            if not account:
                return {"status": "error", "message": "Account not found."}

            try:
                account.balance += amount
                session.commit()

                return {
                    "status": "success",
                    "message": f"₹{amount} refunded.",
                    "new_balance": account.balance
                }

            except Exception as e:
                session.rollback()
                return {
                    "status": "error",
                    "message": f"Refund failed: {str(e)}"
                }
