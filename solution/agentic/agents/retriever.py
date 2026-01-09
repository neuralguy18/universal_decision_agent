# agentic/agents/retriever.py
"""
Retriever agent - RAG retrieval handling.
This module offers:
- extraction of query (simple summarizer) -- placeholder for LLM-based query expansion
- vector lookup using MemoryRepository (SQLAlchemy + PGVector when available)
- fallback naive keyword search over KB folder for small-scale testing
"""

from typing import List, Dict, Any
from ..memory.memory_repo import MemoryRepository
from pathlib import Path
import os

# FIXED: Reliable path to KB folder - use absolute path from solution directory
_CURRENT_FILE = Path(__file__).resolve()
_SOLUTION_DIR = _CURRENT_FILE.parent.parent.parent  # Navigate up from agentic/agents to solution
KB_DIR = _SOLUTION_DIR / "data" / "external" / "kb"

# Debug line — keep for now, remove later
print(f"KB Directory: {KB_DIR}")
print(f"KB Files: {list(KB_DIR.glob('**/*.txt')) if KB_DIR.exists() else 'KB directory does not exist'}")

class Retriever:
    def __init__(self, memory_repo: MemoryRepository = None, top_k: int = 5):
        self.memory_repo = memory_repo
        self.top_k = top_k

    def make_query(self, ticket_text: str) -> str:
        # placeholder: short extraction -- replace with LLM-based expansion
        tokens = ticket_text.strip().split()
        return " ".join(tokens[:20])

    def retrieve(self, ticket: Dict[str, Any]) -> List[Dict[str, Any]]:
        q = self.make_query(ticket.get("text", ""))
        results = []
        # 1) search long-term memory (embeddings) if repository provided
        if self.memory_repo is not None:
            mem_hits = self.memory_repo.semantic_search(q, top_k=self.top_k)
            for row, score in mem_hits:
                results.append({"source": "memory", "id": row.id, "score": float(score), "text": row.text, "metadata": row.metadata_json})
            if results:
                return results
        # 2) naive KB search fallback
        for p in KB_DIR.glob("**/*.txt"):
            txt = p.read_text(encoding="utf8").lower()
            if any(tok in txt for tok in q.lower().split()[:6]):
                snippet = txt[:400]
                results.append({"source":"kb", "id": str(p), "score": 0.5, "text": snippet, "metadata": {"path": str(p)}})
                if len(results) >= self.top_k:
                    break
        return results
