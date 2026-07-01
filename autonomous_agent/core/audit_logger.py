"""Audit logging system with rollback support."""

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from autonomous_agent.core.config import get_config

Base = declarative_base()
logger = logging.getLogger(__name__)


class AuditLog(Base):
    """Audit log database model."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    repository = Column(String(200))
    details = Column(JSON)
    rollback_instructions = Column(JSON)
    status = Column(String(50), default="completed")


class AuditLogger:
    """Audit logger for tracking all agent actions."""

    def __init__(self, config: dict | None = None, log_dir: str | None = None):
        """Initialize audit logger."""
        effective_config = config if config is not None else get_config()

        if log_dir is not None:
            self.log_dir = Path(log_dir)
        elif hasattr(effective_config, "logging") and hasattr(
            effective_config.logging, "log_dir"
        ):
            self.log_dir = Path(effective_config.logging.log_dir)
        else:
            self.log_dir = Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        db_url = f"sqlite:///{self.log_dir / 'audit.db'}"
        if (
            log_dir is None
            and hasattr(effective_config, "database")
            and hasattr(effective_config.database, "url")
        ):
            db_url = effective_config.database.url

        connect_args: dict[str, Any] = {}
        if db_url.startswith("sqlite"):
            # Enable multithreaded sqlite writes for concurrent test execution.
            connect_args["check_same_thread"] = False

        self.engine = create_engine(db_url, connect_args=connect_args)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._file_lock = Lock()
        self.log_file = self.log_dir / "audit.log"

    def log_action(
        self,
        agent_name: str,
        action: str,
        repository: str | None = None,
        details: dict[str, Any] | None = None,
        rollback_instructions: dict[str, Any] | None = None,
    ) -> int:
        """Log an agent action."""
        log_entry = AuditLog(
            agent_name=agent_name,
            action=action,
            repository=repository,
            details=details or {},
            rollback_instructions=rollback_instructions or {},
        )
        session = self.session_factory()
        try:
            session.add(log_entry)
            session.commit()
            self._append_text_log(log_entry)
            return log_entry.id
        finally:
            session.close()

    def get_logs(
        self,
        agent_name: str | None = None,
        repository: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Retrieve audit logs with optional filtering."""
        session = self.session_factory()
        query = session.query(AuditLog)

        try:
            if agent_name:
                query = query.filter(AuditLog.agent_name == agent_name)
            if repository:
                query = query.filter(AuditLog.repository == repository)

            return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def get_rollback_instructions(self, log_id: int) -> dict[str, Any]:
        """Get rollback instructions for a specific action."""
        session = self.session_factory()
        try:
            log = session.query(AuditLog).filter(AuditLog.id == log_id).first()
            return log.rollback_instructions if log else {}
        finally:
            session.close()

    def _append_text_log(self, entry: AuditLog) -> None:
        """Append a JSON line mirror entry to the filesystem audit log."""
        payload = {
            "id": entry.id,
            "timestamp": entry.timestamp.isoformat(),
            "agent_name": entry.agent_name,
            "action": entry.action,
            "repository": entry.repository,
            "details": entry.details or {},
            "rollback_instructions": entry.rollback_instructions or {},
            "status": entry.status,
        }
        try:
            with self._file_lock:
                with open(self.log_file, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, default=str) + "\n")
        except OSError as exc:
            logger.warning("Failed to append text audit log entry: %s", exc)
