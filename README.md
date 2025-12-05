# UDA-Hub: Intelligent Multi-Agent Decision Suite

UDA-Hub is a modular, LangGraph-powered multi-agent system designed to intelligently resolve customer support tickets across multiple platforms.

## Project Structure

solution/  
├── agentic/  
│   ├── agents/           # Custom agents: Classifier, Resolver, Supervisor, Escalation, Auditor  
│   ├── design/           # Architecture and design docs (architecture.md, langgraph_nodes.md, rag_and_memory.md)  
│   ├── memory/           # Memory models and repositories  
│   ├── tools/            # Tools like refund, send_email  
│   └── workflow.py       # Graph orchestration logic  
├── data/  
│   ├── core/             # Core databases (udahub.db)  
│   ├── external/         # External sources (cultpass.jsonl, etc.)  
│   └── models/           # SQLAlchemy ORM models  
├── utils.py              # Utility functions: now_iso, new_id, etc.  
├── 01_external_db_setup.ipynb  
├── 02_core_db_setup.ipynb  
├── 03_agentic_app.ipynb  
└── .env                  # Environment variables  

## Key Features

- **Multi-Agent Architecture**: Specialized agents: Supervisor, Classifier, Resolver, Escalation, Auditor.  
- **Input Handling**: Accepts tickets in natural language with metadata (platform, urgency, history).  
- **Decision Routing & Resolution**: Routes tickets to correct agent based on classification, retrieves relevant knowledge using RAG if needed, resolves or escalates based on confidence and context.  
- **Memory Integration**: Short-term memory (session/thread context), Long-term memory (semantic search for storing preferences and history).  
- **Tool Integration**: Executes internal tools like refunds or sends emails when allowed.  

## Getting Started

Follow these steps to run the project locally.

### Dependencies

- Python >= 3.10  
- pip  
- sqlalchemy  
- langchain-core  
- langgraph  
- python-dotenv  

### Installation

1. Clone the repository:  
`git clone <repo-url>`  
`cd universal_decision_agent/solution`  

2. Install dependencies:  
`pip install -r requirements.txt`  

3. Create a `.env` file with:  
 MEMORY_DB_URL=sqlite:///./data/core/udahub.db
DEFAULT_CONFIDENCE_THRESHOLD=0.75


## Testing

Run the workflow with a sample ticket:

```python
from agentic.workflow import orchestrator
from utils import new_id, now_iso

ticket = {
    "ticket_id": new_id(),
    "platform": "email",
    "user_id": "user_abc",
    "text": "I want a refund for my order 12345. I never received it.",
    "metadata": {"urgency":"medium", "language":"en", "thread_id": "thread_1"},
    "attachments": [],
    "created_at": now_iso()
}

output = orchestrator(ticket, session_id="thread_1", dry_run=True)
print(output["audit"])


Break Down Tests

The orchestrator function runs the full multi-agent pipeline:

    - Classification

    - Retrieval of relevant knowledge (RAG)

    - Resolution

    - Supervisor checks and decision

    - Tool execution (if allowed)

    - Auditing

dry_run=True ensures no real actions are performed.


##Project Instructions

    - Develop agents inside agentic/agents/ and tools inside agentic/tools/.

    - Orchestration logic is inside agentic/workflow.py.

    - Memory handling: Short-term memory: session/thread context, Long-term memory: semantic search using SQLAlchemy.

    - Design documentation is located under agentic/design/: architecture.md, langgraph_nodes.md, rag_and_memory.md.

## Workflow Overview
[Incoming Ticket] 
        │
        ▼
   [Classifier] --> decides category & recommended tools
        │
        ▼
   [Decision Pre-check] --> requires knowledge?
        │ Yes
        ▼
     [Retriever] --> fetch context documents
        │
        ▼
   [Resolver] --> resolves ticket with context
        │
        ▼
   [Supervisor] --> decides auto_resolve or escalate
      ┌──────────────┴──────────────┐
      ▼                             ▼
[Execute Tool(s)]               [Escalate]
      │                             │
      ▼                             ▼
   [Auditor] ----------------------> [Audit stored]


## Built With

Python

- Programming language

SQLAlchemy

- ORM for memory storage

LangGraph

- Multi-agent orchestration framework

LangChain Core

- Chat message and agent utilities

Dotenv

- Environment variable management


License

MIT License

---

