# Architecture — UDA-Hub Agentic System

## Purpose
High-level architecture for the multi-agent decision engine.

## Components
- **Ingress API** — Normalizes incoming ticket payloads.
- **LangGraph Orchestrator** — Executes agent nodes (classifier, resolver, retriever, etc.).
- **Agents (LLM-driven)**  
  - Supervisor  
  - Classifier  
  - Retriever  
  - Resolver  
  - Escalation agent 
- **Tools** — refund, account_lookup, send_email, label_ticket.
- **Memory (SQLAlchemy-based)**  
  - short_term_memory table  
  - long_term_memory table with embeddings (PGVector)
- **Knowledge Base** — Documents + embeddings.
- **Dashboard** — Human-in-the-loop escalation panel.

## Data Flow
[Webhook/API] -> [Ingest] -> [Orchestrator]
-> Classifier -> Decision -> Retriever -> Resolver -> Tool
-> Escalation -> Dashboard
Memory <-> Orchestrator
KB <-> Retriever
Logger -> DB