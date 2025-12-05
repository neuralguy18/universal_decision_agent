# agentic/memory/memory_models.py
from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Text, JSON, Float
)
from sqlalchemy.orm import registry, relationship, mapped_column, Mapped
from datetime import datetime
import sqlalchemy as sa

mapper_registry = registry()
Base = mapper_registry.generate_base()

class ShortTermMemory(Base):
    __tablename__ = "short_term_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(128), index=True, nullable=False)
    ticket_id = Column(String(128), index=True, nullable=True)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), index=True, nullable=False)
    ticket_id = Column(String(128), index=True, nullable=True)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # prefer PGVector when available
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
