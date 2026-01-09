# agentic/agents/resolver.py
from typing import Dict, Any, List
import sys

class Resolver:
    def __init__(self, llm):
        self.llm = llm

    def resolve(self,
                ticket: Dict[str, Any],
                context_docs: List[Dict[str, Any]] = None,
                allowed_tools: List[str] = None,
                stm_context: List[Dict[str, Any]] = None,
                ticket_messages: List[Dict[str, Any]] = None,
                ltm_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a grounded response using all available context.
        Returns dict with 'response' and 'confidence'.
        """
        context_docs = context_docs or []
        stm_context = stm_context or []
        ticket_messages = ticket_messages or []
        ltm_docs = ltm_docs or []
        allowed_tools = allowed_tools or []

        user_text = ticket.get("text", "")

        # Build rich context
        context_parts = []

        if context_docs:
            kb_text = "\n\n".join([
                f"Title: {d.get('title', 'Article')}\nContent: {d.get('content', d.get('text', ''))}"
                for d in context_docs
            ])
            context_parts.append(f"### Knowledge Base Articles\n{kb_text}")

        if ltm_docs:
            past_cases = "\n\n".join([
                f"Past similar case (score {d['score']:.2f}):\n{d['text']}"
                for d in ltm_docs[:3]
            ])
            context_parts.append(f"### Similar Past Resolved Cases\n{past_cases}")

        if ticket_messages:
            history = "\n".join([
                f"{'User' if m.get('role') == 'user' else 'Agent'}: {m.get('content', m.get('text', ''))}"
                for m in ticket_messages[-6:]
            ])
            context_parts.append(f"### Conversation History\n{history}")

        # If we have context, format it; otherwise, provide instruction for common cases
        if context_parts:
            full_context = "\n\n---\n\n".join(context_parts)
        else:
            # For refund requests, provide default knowledge
            if "refund" in user_text.lower():
                full_context = """### Refund Policy
You can help customers with refund requests. Our policy allows refunds if:
- They cancel within 7 days of purchase
- The class was not attended
- The order was not delivered
For pro-rated refunds on subscriptions, encourage them to proceed."""
            else:
                full_context = "No specific context available. Use general customer service knowledge."

        prompt = f"""
You are a helpful and accurate CultPass customer support agent.

Use the information below to answer the customer's latest message.
Be friendly, concise, and clear.

### Available Tools (only suggest if appropriate):
{', '.join(allowed_tools) if allowed_tools else 'None'}

### Context
{full_context}

### Customer's Latest Message
{user_text}

### Instructions
- Answer directly and naturally
- If the customer is asking for a refund and you have the 'refund' tool, offer to help: "I can help process that refund for you. Would you like me to proceed?"
- Keep response under 200 words
"""

        try:
            response = self.llm.invoke(prompt)
            
            # Handle different response types from LLM (ChatOpenAI returns AIMessage)
            if hasattr(response, 'content'):
                answer = response.content.strip()
            elif isinstance(response, str):
                answer = response.strip()
            else:
                answer = str(response).strip()
            
            # Fallback for empty response
            if not answer or answer == "":
                answer = "Thank you for contacting CultPass support. I'm processing your request. How can I help you further?"

            # Estimate confidence
            base_conf = 0.5
            conf_bonus = 0.1 * len(context_docs) + 0.05 * len(ltm_docs)
            confidence = min(0.95, base_conf + conf_bonus)

            # Suggest actions based on intent
            actions = []
            if "refund" in allowed_tools and "refund" in user_text.lower():
                actions.append({
                    "tool": "refund",
                    "description": "Process refund request",
                    "params": {"order_id": "to_be_provided"}
                })

            return {
                "response": answer,
                "confidence": confidence,
                "sources_used": len(context_docs) + len(ltm_docs),
                "actions": actions
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ RESOLVER ERROR: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            
            # Provide helpful error message
            if "api_key" in error_msg.lower() or "401" in error_msg:
                error_msg_user = "API authentication failed. Please check your OpenAI API key configuration."
            elif "404" in error_msg or "chat model" in error_msg:
                error_msg_user = "Model endpoint error. Please check your LLM_MODEL configuration."
            else:
                error_msg_user = "Error generating response. Please try again."
            
            return {
                "response": f"I'm having trouble generating a response right now. {error_msg_user}",
                "confidence": 0.1,
                "error": error_msg
            }