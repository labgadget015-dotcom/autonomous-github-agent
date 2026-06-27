"""Audit logging system with rollback support."""

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from autonomous_agent.core.config import get_config

Base = declarative_base()


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
        cfg = get_config()
        self.log_dir: Path | None = None
        db_url = "sqlite:///./audit.db"
        if log_dir is not None:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            self.log_dir = log_path
            db_url = f"sqlite:///{log_path}/audit.db"
        elif hasattr(cfg, "database"):
            db_url = cfg.database.url
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

    @property
    def session(self):
        return self.Session()

    def log_action(
        self,
        agent_name: str,
        action: str,
        repository: str | None = None,
        details: dict[str, Any] | None = None,
        rollback_instructions: dict[str, Any] | None = None,
    ) -> int:
        """Log an agent action."""
        session = self.Session()
        log_entry = AuditLog(
            agent_name=agent_name,
            action=action,
            repository=repository,
            details=details or {},
            rollback_instructions=rollback_instructions or {},
        )
        session.add(log_entry)
        session.commit()
        return log_entry.id

    def get_logs(
        self,
        agent_name: str | None = None,
        repository: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Retrieve audit logs with optional filtering."""
        query = self.Session().query(AuditLog)

        if agent_name:
            query = query.filter(AuditLog.agent_name == agent_name)
        if repository:
            query = query.filter(AuditLog.repository == repository)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    def get_rollback_instructions(self, log_id: int) -> dict[str, Any]:
        """Get rollback instructions for a specific action."""
        log = self.Session().query(AuditLog).filter(AuditLog.id == log_id).first()
        return log.rollback_instructions if log else {}
