# 🤖 UDA-Hub — Universal Decision Agent

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Powered-00D084?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com)

*A LangGraph-powered multi-agent system that intelligently classifies, routes, resolves, and escalates customer support tickets with built-in RAG, shared memory, tool execution, and audit trails.*

[🚀 Quick Start](#-quick-start) • [📚 Documentation](#-documentation) • [💡 Features](#-features) • [🛠️ Development](#-development)

</div>

---

## 🌟 Overview

**UDA-Hub** is a production-ready multi-agent framework powered by **LangGraph** that intelligently routes, classifies, and resolves customer support tickets. It includes:

- 🎯 **Intelligent routing** with a multi-agent pipeline
- 💾 **Dual memory system** (short-term session context + long-term semantic search)
- 🎨 **Streamlit UI** for easy interaction
- 🔧 **Tool integration** (refunds, email notifications)
- 📊 **Audit trail** for every decision
- ✨ **Graceful fallback** when dependencies are missing

Perfect for building customer support bots, help desk automation, and decision-support systems.  

---

## 💡 Features

| Feature | Description |
|---------|-------------|
| 🧠 **Multi-Agent Pipeline** | Specialized agents: Classifier → Resolver → Supervisor → Escalation → Auditor |
| 🗣️ **Natural Language** | Accept support tickets in plain text with rich metadata |
| 🔍 **Smart Routing** | Classifies intent, retrieves relevant knowledge, routes to best handler |
| 💬 **Memory System** | STM (per-session context) + LTM (semantic search with embeddings) |
| 🎛️ **Tool Ecosystem** | Built-in refunds, email, and extensible tool framework |
| 📈 **Confidence Scoring** | Transparent confidence levels for every resolution |
| 🔐 **Audit Trail** | Complete decision log for compliance and debugging |
| 🎯 **Fallback Mode** | Graceful degradation when optional dependencies missing |  

---

## 📋 Requirements

- **Python** 3.10 or higher
- **pip** package manager
- **SQLite** (included with Python) or **PostgreSQL** (for production)

## 🚀 Quick Start

### 1️⃣ Clone & Install

```bash
# Navigate to the solution directory
cd universal_decision_agent/solution

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure (Optional)

Create a `solution/.env` file:

```env
# Database (SQLite by default)
MEMORY_DB_URL=sqlite:///./data/core/memory.sqlite

# Agent settings
DEFAULT_CONFIDENCE_THRESHOLD=0.75

# LLM (if using GPT integrations)
LLM_MODEL=gpt-3.5-turbo
LLM_TEMP=0
OPENAI_API_KEY=sk-...
```

### 3️⃣ Launch the UI

```bash
cd solution
streamlit run app.py
```

The Streamlit app opens at `http://localhost:8501` — start chatting! 💬


---

## 📖 How It Works

### 🔄 The Agent Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                   [Your Message]                        │
│                        │                                │
│                        ▼                                │
│        ┌──────────────────────────────┐                │
│        │      Classifier Agent        │                │
│        │  (Intent, Category, Tools)   │                │
│        └──────────────────────────────┘                │
│                        │                                │
│                        ▼                                │
│        ┌──────────────────────────────┐                │
│        │   Knowledge Retriever (RAG)  │                │
│        │   (Find relevant docs)       │                │
│        └──────────────────────────────┘                │
│                        │                                │
│                        ▼                                │
│        ┌──────────────────────────────┐                │
│        │   Resolver Agent             │                │
│        │   (Generate response)        │                │
│        └──────────────────────────────┘                │
│                        │                                │
│                        ▼                                │
│        ┌──────────────────────────────┐                │
│        │   Supervisor Agent           │                │
│        │   (Auto-resolve or escalate?)│                │
│        └──────────────────────────────┘                │
│          ┌────────────────┬─────────────┐             │
│          ▼                ▼             ▼             │
│     [Execute]         [Escalate]    [Finalize]       │
│      Tools           Support Team    & Audit         │
│                                                      │
└─────────────────────────────────────────────────────────┘
```

### 🧠 Memory Architecture

| Layer | Purpose | Storage | Retention |
|-------|---------|---------|-----------|
| **STM** 📝 | Session context, chat history | SQLite | Session-based |
| **LTM** 🧠 | Resolved tickets, embeddings | SQLite + vectors | Persistent |

Messages are **automatically persisted** — reload the page and continue where you left off!

---

## 📁 Project Structure

```
universal_decision_agent/
│
├── solution/                          # Main application
│   ├── app.py                         # 🎨 Streamlit UI
│   ├── utils.py                       # 🛠️ Helper utilities
│   ├── requirements.txt               # 📦 Dependencies
│   │
│   ├── agentic/                       # 🧠 Agent logic
│   │   ├── agents/
│   │   │   ├── classifier.py          # 📂 Intent classification
│   │   │   ├── resolver.py            # 💡 Response generation
│   │   │   ├── supervisor.py          # 👨‍⚖️ Decision making
│   │   │   ├── escalation.py          # 📢 Escalation logic
│   │   │   └── auditor.py             # 📊 Audit logging
│   │   │
│   │   ├── memory/
│   │   │   ├── memory_models.py       # 🗄️ SQLAlchemy ORM
│   │   │   └── memory_repo.py         # 💾 DB operations
│   │   │
│   │   ├── tools/
│   │   │   ├── refund.py              # 💰 Refund tool
│   │   │   └── send_email.py          # 📧 Email tool
│   │   │
│   │   ├── workflow.py                # 🔗 LangGraph orchestration
│   │   └── embeddings.py              # 🔢 Embedding service
│   │
│   ├── data/
│   │   ├── core/
│   │   │   ├── memory.sqlite          # 💾 Memory database
│   │   │   └── audit/audit.jsonl      # 📋 Audit logs
│   │   └── external/
│   │       └── cultpass_*.jsonl       # 📄 Sample data
│   │
│   └── notebooks/
│       ├── 01_external_db_setup.ipynb # Setup external data
│       ├── 02_core_db_setup.ipynb     # Setup core DB
│       └── 03_agentic_app.ipynb       # Full workflow demo
│
├── README.md                          # 📖 This file
└── .env.example                       # ⚙️ Config template
```

---

## 🎯 Usage Examples

### 💬 Interactive Chat (Streamlit)

```bash
cd solution
streamlit run app.py
```

Then type support requests like:
- "I want a refund for order #12345"
- "How do I reset my password?"
- "I haven't received my order yet"

### 🐍 Programmatic Usage

```python
from agentic.workflow import orchestrator
from utils import new_id, now_iso

# Create a ticket
ticket = {
    "ticket_id": new_id(),
    "platform": "api",
    "user_id": "user_123",
    "text": "My refund hasn't arrived after 5 days!",
    "metadata": {
        "urgency": "high",
        "language": "en",
        "thread_id": "support_session_xyz"
    },
    "attachments": [],
    "created_at": now_iso()
}

# Run the full agent pipeline
result = orchestrator(ticket, session_id="support_session_xyz")

# Inspect the decision
print(f"Resolution: {result['resolver']['response']}")
print(f"Auto-resolved: {result['decision']['auto_resolve']}")
print(f"Confidence: {result['resolver']['confidence']:.0%}")
print(f"Audit: {result['audit']}")
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_DB_URL` | `sqlite:///./data/core/memory.sqlite` | Database connection string |
| `DEFAULT_CONFIDENCE_THRESHOLD` | `0.75` | Min confidence to auto-resolve |
| `LLM_MODEL` | `gpt-3.5-turbo` | LLM model to use |
| `LLM_TEMP` | `0` | LLM temperature (0=deterministic) |
| `OPENAI_API_KEY` | - | OpenAI API key (if using GPT) |

### Database

By default, data is stored in **SQLite**. For production, use **PostgreSQL**:

```env
MEMORY_DB_URL=postgresql://user:password@localhost:5432/uda_hub
```

---

## 📚 Documentation

### Architecture

See [agentic/design/architecture.md](solution/agentic/design/architecture.md) for:
- Detailed agent responsibilities
- Graph topology
- State schema

### LangGraph Nodes

See [agentic/design/langgraph_nodes.md](solution/agentic/design/langgraph_nodes.md) for:
- Node definitions
- Edge routing logic
- Conditional branches

### Memory & RAG

See [agentic/design/rag_and_memory.md](solution/agentic/design/rag_and_memory.md) for:
- STM architecture
- LTM semantic search
- Embedding strategy

---

## 🐛 Troubleshooting

### ❓ Fallback responses ("I received your message")

**Cause:** The full `agentic.workflow` failed to import.

**Solution:**
1. Check the Streamlit logs for the error
2. Install missing packages: `pip install -r requirements.txt`
3. Verify environment variables are set correctly

### ❓ Memory database errors

**Cause:** Database file is locked or path doesn't exist.

**Solution:**
```bash
# Check DB permissions
ls -la solution/data/core/memory.sqlite

# Reset DB (deletes history!)
rm solution/data/core/memory.sqlite
```

### ❓ LLM API errors

**Cause:** API key missing or invalid.

**Solution:**
```bash
# Export your API key
export OPENAI_API_KEY=sk-...

# Verify it's set
echo $OPENAI_API_KEY
```

---

## 🛠️ Development

### Adding a New Agent

1. Create `solution/agentic/agents/my_agent.py`
2. Inherit from base Agent class
3. Implement `__call__` or `resolve` method
4. Add to workflow in `solution/agentic/workflow.py`

### Adding a Tool

1. Create `solution/agentic/tools/my_tool.py`
2. Implement `call(params: dict, dry_run: bool) -> dict`
3. Register in Resolver agent
4. Test with notebook

### Running Tests

```bash
cd solution
python -m pytest tests/  # (if you have tests)
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Commit** changes: `git commit -m "Add my feature"`
4. **Push** to branch: `git push origin feature/my-feature`
5. **Open** a Pull Request

Please include:
- Clear description of changes
- Test coverage (if applicable)
- Updated documentation

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

---

## 🎓 Learning Resources

- [LangGraph Docs](https://python.langchain.com/docs/langgraph)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

---

## 💬 Support & Feedback

- **Issues?** Open a [GitHub Issue](https://github.com)
- **Questions?** Start a [Discussion](https://github.com)
- **Ideas?** Submit a [Feature Request](https://github.com)

---

<div align="center">

**Made with ❤️ for intelligent customer support**

⭐ If you find this useful, please star the repository!

</div>
