# agentic/agents/resolver.py
from typing import Dict, Any, List

class Resolver:
    def __init__(self, llm):
        self.llm = llm

    def resolve(self, ticket: str, context_docs: list):
        """Generate KB-grounded answer using retrieved documents."""

        if not context_docs:
            # No knowledge → very low confidence
            return {
                "answer": "I could not locate relevant information in the knowledge base.",
                "confidence": 0.2
            }

        # Combine KB articles
        context_text = "\n\n---\n\n".join(
            [f"Title: {doc['title']}\nContent: {doc['content']}"
             for doc in context_docs]
        )

        prompt = f"""
You are a support agent. Use ONLY the context below to answer the question.
If context does not contain the answer, say "The knowledge base does not contain this information."

### CONTEXT
{context_text}

### QUESTION
{ticket}

### INSTRUCTIONS
- Use KB content directly
- Do NOT hallucinate
- Keep response concise
"""

        response = self.llm.invoke(prompt)
        answer = response.strip()

        # Confidence grows with number + similarity of matches
        confidence = min(0.95, 0.5 + 0.1 * len(context_docs))

        return {
            "answer": answer,
            "confidence": confidence
        }

