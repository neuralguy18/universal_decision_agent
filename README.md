# UDA-Hub: Intelligent Multi-Agent Customer Support Suite
![Static Badge](https://img.shields.io/badge/Python-3.10%2B%20-blue)  ![Static Badge](https://img.shields.io/badge/LangGraph-Latest%20-green) ![Static Badge](https://img.shields.io/badge/License-MIT%20-yellow) ![Static Badge](https://img.shields.io/badge/Streamlit-Latest%20-orange)

A LangGraph-powered multi-agent system that intelligently classifies, routes, resolves, and escalates customer support tickets with built-in RAG, shared memory, tool execution, and audit trails.

## Project Overview

UDA-Hub is a personal prototype I developed during my career break to demonstrate agentic AI in enterprise customer support workflows.
This modular multi-agent system mimics a real-world support operations center:
    - Accepts natural-language tickets with metadata (platform, urgency, history)
    - Classifies intent and severity
    - Retrieves relevant knowledge via RAG
    - Attempts autonomous resolution using tools (e.g., refund, email)
    - Escalates when needed with clear reasoning
    - Maintains short-term (thread) and long-term (semantic) memory
    - Audits every decision for traceability and continuous improvement

### Key outcomes from simulations
  
  - Achieved ~85% first-contact resolution in test scenarios (refund, status, complaints)
  - Reduced escalation rate to <15% through confidence-based supervisor routing
  - Full audit trail enables post-hoc analysis and agent refinement

This project showcases production-grade agentic patterns: stateful orchestration, safe tool calling, handoffs, and memory management — directly applicable to AI-native enterprise SaaS support platforms.

### Key Features

  - **Specialized Agents**: Classifier → Retriever → Resolver → Supervisor → Escalation → Auditor
  - **Dynamic Routing**: Supervisor decides auto-resolve vs. escalate based on confidence and policy
  - **RAG Integration**: Retrieves internal knowledge (policies, FAQs, past resolutions)
  - **Memory Layers**
    - Short-term: Thread/session context
    - Long-term: Semantic search over resolved tickets and user preferences
  - **Safe Tool Execution**: Refunds, send email, etc. (dry-run mode by default)
  - **Comprehensive Auditing**: Logs classification, reasoning, tools used, and final decision

## Architecture

<img width="568" height="730" alt="image" src="https://github.com/user-attachments/assets/cbfaeea2-390a-4c81-a8be-85a2c5371cb5" />


## Example Interaction
```
ticket = {
    "ticket_id": "tkt_001",
    "platform": "email",
    "user_id": "user_abc",
    "text": "I want a refund for order 12345. I never received it.",
    "metadata": {"urgency": "high"},
    "created_at": "2025-12-22T10:00:00Z"
}

result = orchestrator(ticket, session_id="thread_1", dry_run=True)
```

### Sample output (dry run)
```
{
  "classification": {"category": "refund", "recommended_tools": ["process_refund"]},
  "resolution": "Eligible for full refund per policy",
  "supervisor_decision": "auto_resolve",
  "tools_executed": ["process_refund (simulated)"],
  "audit": "Refund approved – policy matched, no prior refunds, urgency high"
}
```

## Tech Stack

  - **LangGraph** : Stateful multi-agent orchestration and graph workflow
  - **LangChain Core** : Agents, tools, memory, and message handling
  - **SQLAlchemy + SQLite** : Core database for long-term memory and audits
  - **Python-dotenv** : Configuration management
  - **Streamlit** : Interaction for users

## Project Structure
```
uda-hub/
├── agentic/
│   ├── agents/          # Classifier, Resolver, Supervisor, Escalation, Auditor
│   ├── tools/           # refund_tool, send_email_tool, etc.
│   ├── memory/          # Short-term and long-term memory implementations
│   └── workflow.py      # Main LangGraph orchestration
├── data/
│   ├── core/            # udahub.db (SQLite)
│   └── external/        # Sample knowledge sources for RAG
├── notebooks/
│   ├── 01_external_db_setup.ipynb
│   ├── 02_core_db_setup.ipynb
│   └── 03_agentic_app.ipynb       # Interactive testing
├── utils.py             # Helpers (ID generation, timestamps)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & Quick Start

**1.Clone the repository**
```
git clone https://github.com/yourusername/uda-hub.git
cd uda-hub/solution
```

**2.Install dependencies**
```
pip install -r requirements.txt
```

**3.Set Environment variables**
```
MEMORY_DB_URL=sqlite:///./data/core/udahub.db
DEFAULT_CONFIDENCE_THRESHOLD=0.75
OPENAI_API_KEY=your_key
```

**4.Launch UI**
```
cd solution
streamlit run app.py
```


The Streamlit app opens at `http://localhost:8501` — start chatting!
Then type support requests like:
- "I want a refund for order #12345"
- "How do I reset my password?"
- "I haven't received my order yet"


**5.Programmatic use**
```
from agentic.workflow import orchestrator
```


## Future Enhancements (Roadmap Ideas)
  - Integrate real ticketing APIs (Zendesk, Freshdesk)
  - Add human-in-the-loop approval node
  - Dashboard for audit analytics and agent performance
  - Multi-language support via translation tools


## License
MIT License – free to fork, extend, or use as reference.
Built by Pravir Sinha | December 2025




</div>
