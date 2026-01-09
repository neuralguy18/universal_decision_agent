# app.py
import streamlit as st
from dotenv import load_dotenv
from utils import new_id, now_iso
import traceback
from agentic.memory.memory_repo import MemoryRepository

load_dotenv()

st.set_page_config(page_title="CultPass AI Support Agent", page_icon="🤖", layout="centered")

st.title("🤖 CultPass AI Support Agent")
st.caption("Powered by your agentic workflow • Smart • Safe • Auditable")

# Sidebar control for showing confidence
# Using `st.sidebar.checkbox` so it's available before messages render
show_confidence = st.sidebar.checkbox("Show agent confidence (%)", value=False)

# === CRITICAL FIX: Cache the compiled workflow so it's the SAME across reruns ===
@st.cache_resource(show_spinner="Initializing AI agent...")
def get_workflow():
    # Try to import the real compiled workflow from the package. If that fails
    # (missing deps), return a lightweight dummy workflow with an `invoke`
    # method so the Streamlit UI still loads and responds.
    try:
        from agentic.workflow import workflow as real_workflow  # type: ignore
        return real_workflow
    except Exception:
        # Provide a simple fallback that mimics the invoke API used below.
        class DummyWorkflow:
            def invoke(self, initial_state, config=None):
                ticket = initial_state.get("ticket", {})
                text = ticket.get("text", "")
                # Simple echo-like response
                response = f"(Fallback) I received your message: {text}"
                return {"resolver_output": {"response": response, "confidence": 0.5}}

        return DummyWorkflow()

compiled_workflow = get_workflow()  # This runs ONLY ONCE

# Initialize memory repository (used for STM/LTM storage and retrieval)
try:
    memory_repo = MemoryRepository()
except Exception:
    memory_repo = None

# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit_demo_thread"
if "messages" not in st.session_state:
    # preload messages from short-term memory if available
    st.session_state.messages = []
    try:
        if memory_repo:
            past = memory_repo.get_ticket_messages(session_id=st.session_state.thread_id, limit=100)
            for m in past:
                role = m.get("role", "user")
                text = m.get("text") or m.get("message") or ""
                if text:
                    st.session_state.messages.append({"role": role, "content": text})
    except Exception:
        # ignore memory load failures
        pass

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create ticket
    ticket = {
        "ticket_id": new_id(),
        "platform": "streamlit",
        "user_id": "streamlit_user_1",
        "text": prompt,
        "metadata": {"thread_id": st.session_state.thread_id, "urgency": "medium"},
        "created_at": now_iso(),
        "attachments": [],
    }

    # Store user message into STM
    try:
        if memory_repo:
            memory_repo.put_ticket_message(session_id=st.session_state.thread_id, ticket_id=ticket["ticket_id"], from_role="user", text=prompt, metadata={"created_at": ticket["created_at"]})
    except Exception:
        pass

    # Show thinking spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Use the CACHED workflow to invoke
            had_error = False
            try:
                result_state = compiled_workflow.invoke(
                    {"ticket": ticket},
                    config={"configurable": {"thread_id": st.session_state.thread_id}}
                )
                resolver_out = result_state.get("resolver_output", {}) or {}
            except Exception as e:
                # Present a readable error in the UI but keep the app running
                tb = traceback.format_exc()
                resolver_out = {"response": "An error occurred while processing the request.", "confidence": 0.0}
                assistant_text = f"""**Error**: {str(e)}

```
{tb}
```"""
                st.markdown(assistant_text)
                # Save assistant error message and skip normal display
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                had_error = True

            if not had_error:
                assistant_text = (
                    resolver_out.get("response") or
                    resolver_out.get("message") or
                    resolver_out.get("answer") or
                    "I'm sorry, I couldn't generate a response."
                )

                # store assistant message in STM
                try:
                    if memory_repo:
                        memory_repo.put_ticket_message(session_id=st.session_state.thread_id, ticket_id=ticket["ticket_id"], from_role="agent", text=assistant_text, metadata={"created_at": now_iso()})
                except Exception:
                    pass

            # Add confidence info only if user requested it in sidebar
            confidence = resolver_out.get("confidence")
            if show_confidence and confidence is not None:
                confidence_pct = f"{confidence:.0%}"
                assistant_text = assistant_text + f"\n\n*Confidence: {confidence_pct}*"

            # Label the assistant as 'Agent' in the message body
            assistant_text = f"**Agent:**\n\n{assistant_text}"

            st.markdown(assistant_text)

    # Save assistant message (avoid duplicating when an error already appended)
    if not locals().get("had_error", False):
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

# Sidebar remains the same
with st.sidebar:
    st.header("🛠️ Debug Info")
    st.write(f"Thread ID: `{st.session_state.thread_id}`")
    st.write(f"Messages: {len(st.session_state.messages)}")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()