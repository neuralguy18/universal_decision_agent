# agentic/memory/memory_repo.py
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session
import os
import numpy as np
from .memory_models import ShortTermMemory, LongTermMemory, Base
from typing import List, Tuple
from utils import now_iso, new_id



DEFAULT_SQLITE = "sqlite:///./data/core/memory.sqlite"

class MemoryRepository:
    def __init__(self, db_url: str = None, echo: bool = False):
        self.db_url = db_url or os.environ.get("MEMORY_DB_URL") or DEFAULT_SQLITE
        self.engine = create_engine(self.db_url, echo=echo, future=True)
        Base.metadata.create_all(self.engine)

    # Short-term memory
    def put_short(self, session_id: str, ticket_id: str, payload: dict):
        with Session(self.engine) as s:
            row = ShortTermMemory(session_id=session_id, ticket_id=ticket_id, payload_json=payload)
            s.add(row)
            s.commit()
            return row

    def get_short(self, session_id: str):
        with Session(self.engine) as s:
            stmt = select(ShortTermMemory).where(ShortTermMemory.session_id == session_id).order_by(ShortTermMemory.created_at.desc())
            return [r[0] for r in s.execute(stmt).all()]

    # Long-term memory: store text + embedding
    def put_long(self, user_id: str, ticket_id: str, text: str, embedding: List[float], metadata: dict = None):
        with Session(self.engine) as s:
            row = LongTermMemory(user_id=user_id, ticket_id=ticket_id, text=text, embedding=embedding, metadata_json=metadata)
            s.add(row)
            s.commit()
            return row

    def semantic_search(self, query_text: str, top_k: int = 5):
        """
        Simple python fallback: compute embeddings (via embedding_fn) then cosine against stored JSON embeddings.
        If using Postgres+PGVector, replace this with SQL vector operator for efficient search.
        Returns list of tuples (row, score)
        """
        from ..embeddings import embedding_fn
        q_emb = embedding_fn(query_text)
        hits = []
        with Session(self.engine) as s:
            stmt = select(LongTermMemory).where(LongTermMemory.deleted_at.is_(None))
            rows = [r[0] for r in s.execute(stmt).all()]
            for r in rows:
                if not r.embedding:
                    continue
                # numpy dot/cosine
                a = np.array(r.embedding, dtype=float)
                b = np.array(q_emb, dtype=float)
                # cosine similarity
                score = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
                hits.append((r, score))
        hits.sort(key=lambda x: x[1], reverse=True)
        return hits[:top_k]

    # Ticket messages (store conversational messages associated with a session/ticket)
    def put_ticket_message(self, session_id: str = None, ticket_id: str = None, from_role: str = "user", text: str = "", metadata: dict = None):
        with Session(self.engine) as s:
            payload = {"role": from_role, "text": text, "metadata": metadata or {}, "ticket_id": ticket_id, "created_at": now_iso()}
            row = ShortTermMemory(session_id=session_id or "", ticket_id=ticket_id, payload_json=payload)
            s.add(row)
            s.commit()
            return row

    def get_ticket_messages(self, session_id: str = None, user_id: str = None, ticket_id: str = None, limit: int = 50):
        results = []
        with Session(self.engine) as s:
            stmt = select(ShortTermMemory)
            if session_id:
                stmt = stmt.where(ShortTermMemory.session_id == session_id)
            elif ticket_id:
                stmt = stmt.where(ShortTermMemory.ticket_id == ticket_id)
            # order oldest first
            stmt = stmt.order_by(ShortTermMemory.created_at.asc()).limit(limit)
            rows = [r[0] for r in s.execute(stmt).all()]
            for r in rows:
                results.append(r.payload_json if hasattr(r, "payload_json") else {})

        # If no session/ticket messages and user_id provided, try returning LTM entries as historical messages
        if not results and user_id:
            with Session(self.engine) as s:
                stmt2 = select(LongTermMemory).where(LongTermMemory.user_id == user_id).order_by(LongTermMemory.created_at.desc()).limit(limit)
                rows2 = [r[0] for r in s.execute(stmt2).all()]
                for r in rows2:
                    results.append({"role": "ltm", "text": getattr(r, "text", ""), "metadata": getattr(r, "metadata_json", {})})

        return results
