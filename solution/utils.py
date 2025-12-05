import os
import json
import uuid
from datetime import datetime

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def new_id() -> str:
    return str(uuid.uuid4())

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def save_json(obj, path: str):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)

# reset_udahub.py
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from langchain_core.messages import (
    SystemMessage,
    HumanMessage, 
)
from langgraph.graph.state import CompiledStateGraph


Base = declarative_base()

def reset_db(db_path: str, echo: bool = True):
    """Drops the existing udahub.db file and recreates all tables."""

    # Remove the file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing {db_path}")

    # Create a new engine and recreate tables
    engine = create_engine(f"sqlite:///{db_path}", echo=echo)
    Base.metadata.create_all(engine)
    print(f"✅ Recreated {db_path} with fresh schema")


@contextmanager
def get_session(engine: Engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def model_to_dict(instance):
    """Convert a SQLAlchemy model instance to a dictionary."""
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }

from typing import Callable

def chat_interface(orchestrator_func: Callable, ticket_id: str):
    """
    Interactive chat interface for a ticket.
    Directly uses the orchestrator function.
    """
    print(f"Starting chat for Thread ID: {ticket_id}")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Assistant: Goodbye!")
            break

        # Create a ticket dict as expected by orchestrator
        ticket = {
            "ticket_id": ticket_id,
            "text": user_input,
            "user_id": "user_1",
            "platform": "chat",
            "metadata": {"thread_id": ticket_id},
            "attachments": [],
        }

        # Call orchestrator directly
        result = orchestrator_func(ticket, session_id=ticket_id)

        # Print assistant's response
        resolver_out = result.get("resolver") or {}
        assistant_text = resolver_out.get("response") or resolver_out.get("message") or "No response generated."
        print("Assistant:", assistant_text)

