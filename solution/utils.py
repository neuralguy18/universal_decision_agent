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

from typing import Callable, Optional, List

def chat_interface(orchestrator_func: Callable, ticket_id: str, prompts: Optional[List[str]] = None):
    """
    Chat interface for a ticket. By default runs interactively using `input()`.

    If `prompts` is provided (a list of strings), the function will run non-interactively
    by sending each prompt to the `orchestrator_func` in order and printing responses.

    This makes it safe to use in notebooks and CI where stdin may not be available.
    """
    print(f"Starting chat for Thread ID: {ticket_id}")

    def _run_turn(user_input: str):
        ticket = {
            "ticket_id": ticket_id,
            "text": user_input,
            "user_id": "user_1",
            "platform": "chat",
            "metadata": {"thread_id": ticket_id},
            "attachments": [],
        }
        result = orchestrator_func(ticket, session_id=ticket_id)
        resolver_out = result.get("resolver") or {}
        assistant_text = resolver_out.get("response") or resolver_out.get("message") or "No response generated."
        print("Assistant:", assistant_text)

    # Non-interactive mode for notebooks/tests
    if prompts is not None:
        for p in prompts:
            if p.lower() in ["quit", "exit", "q"]:
                print("Assistant: Goodbye!")
                break
            print("User:", p)
            _run_turn(p)
        return

    # Interactive mode (fallback)
    while True:
        try:
            user_input = input("User: ")
        except EOFError:
            # Some notebook frontends don't support stdin; exit gracefully
            print("Assistant: stdin not available — exiting interactive chat.")
            break

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Assistant: Goodbye!")
            break

        _run_turn(user_input)

