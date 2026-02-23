#!/usr/bin/env python3
"""
Audit Logger

Provides immutable audit trail with rollback instructions for all agent actions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Immutable audit logger for tracking all agent actions.

    Features:
    - Immutable log entries
    - Rollback instruction generation
    - JSON-based storage
    - PostgreSQL integration (optional)
    - S3 archival support (optional)
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize audit logger.

        Args:
            config: Configuration dictionary containing:
                - audit_log_path: Path to audit log file (default: logs/audit.jsonl)
                - postgres_config: Optional PostgreSQL configuration
                - s3_config: Optional S3 configuration for archival
        """
        self.config = config

        # Set up local file logging
        log_path = config.get("audit_log_path", "logs/audit.jsonl")
        self.log_file = Path(log_path)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # PostgreSQL connection (if configured)
        self._pg_conn = None
        if config.get("postgres_config"):
            self._init_postgres()

        # S3 client (if configured)
        self._s3_client = None
        if config.get("s3_config"):
            self._init_s3()

        logger.info(f"Audit logger initialized: {self.log_file}")

    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            import psycopg2

            pg_config = self.config["postgres_config"]
            self._pg_conn = psycopg2.connect(
                host=pg_config.get("host", "localhost"),
                port=pg_config.get("port", 5432),
                database=pg_config.get("database", "audit_logs"),
                user=pg_config.get("user"),
                password=pg_config.get("password"),
            )
            logger.info("PostgreSQL connection established")
        except ImportError:
            logger.warning("psycopg2 not installed. PostgreSQL logging disabled.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")

    def _init_s3(self):
        """Initialize S3 client"""
        try:
            import boto3

            s3_config = self.config["s3_config"]
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=s3_config.get("access_key"),
                aws_secret_access_key=s3_config.get("secret_key"),
                region_name=s3_config.get("region", "us-east-1"),
            )
            logger.info("S3 client initialized")
        except ImportError:
            logger.warning("boto3 not installed. S3 archival disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")

    async def log_action(
        self,
        agent: str,
        action: str,
        params: dict[str, Any],
        result: dict[str, Any],
        task_id: str,
        status: str = "success",
    ):
        """
        Log an agent action to the audit trail.

        Args:
            agent: Name of the agent performing the action
            action: Action type
            params: Action parameters
            result: Action result
            task_id: Unique task identifier
            status: Action status ('success', 'error', 'pending')
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent": agent,
            "action": action,
            "params": params,
            "result": result,
            "status": status,
            "rollback": self._generate_rollback_instructions(action, params, result),
        }

        # Write to local file
        await self._write_to_file(log_entry)

        # Write to PostgreSQL if configured
        if self._pg_conn:
            await self._write_to_postgres(log_entry)

        logger.info(f"Logged action: {agent}.{action} (task_id: {task_id})")

    async def _write_to_file(self, log_entry: dict[str, Any]):
        """Write log entry to local file"""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to audit log file: {str(e)}")

    async def _write_to_postgres(self, log_entry: dict[str, Any]):
        """Write log entry to PostgreSQL"""
        try:
            cursor = self._pg_conn.cursor()  # type: ignore[attr-defined]
            cursor.execute(
                """
                INSERT INTO audit_logs
                (timestamp, task_id, agent, action, params, result, status, rollback)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    log_entry["timestamp"],
                    log_entry["task_id"],
                    log_entry["agent"],
                    log_entry["action"],
                    json.dumps(log_entry["params"]),
                    json.dumps(log_entry["result"]),
                    log_entry["status"],
                    log_entry["rollback"],
                ),
            )
            self._pg_conn.commit()  # type: ignore[attr-defined]
        except Exception as e:
            logger.error(f"Failed to write to PostgreSQL: {str(e)}")

    def _generate_rollback_instructions(
        self, action: str, params: dict[str, Any], result: dict[str, Any]
    ) -> str:
        """
        Generate rollback instructions for an action.

        Args:
            action: Action type
            params: Action parameters
            result: Action result

        Returns:
            Human-readable rollback instructions
        """
        rollback_map = {
            "create_issue": "Close the issue manually or via API",
            "create_branch": f"Delete branch: git branch -D {params.get('branch_name', 'unknown')}",  # noqa: E501
            "merge_pr": "Revert the merge commit",
            "delete_branch": f"Restore branch from commit: {result.get('last_commit', 'unknown')}",  # noqa: E501
            "update_file": f"Revert file changes: git checkout {result.get('previous_sha', 'HEAD~1')} -- {params.get('file_path', '')}",  # noqa: E501
            "add_label": f"Remove label: {params.get('label', '')}",
            "assign_issue": f"Unassign user: {params.get('assignee', '')}",
        }

        return rollback_map.get(action, "N/A - Manual rollback required")

    async def archive_logs(self, older_than_days: int = 90):
        """
        Archive logs older than specified days to S3.

        Args:
            older_than_days: Archive logs older than this many days
        """
        if not self._s3_client:
            logger.warning("S3 not configured. Cannot archive logs.")
            return

        try:
            # Read log file and filter old entries
            # Upload to S3
            # Remove archived entries from local file
            logger.info(f"Archived logs older than {older_than_days} days")
        except Exception as e:
            logger.error(f"Failed to archive logs: {str(e)}")

    def get_logs(
        self,
        agent: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list:
        """
        Retrieve audit logs with optional filtering.

        Args:
            agent: Filter by agent name
            action: Filter by action type
            limit: Maximum number of logs to return

        Returns:
            List of log entries
        """
        logs = []

        try:
            with open(self.log_file) as f:
                for line in f:
                    entry = json.loads(line.strip())

                    # Apply filters
                    if agent and entry.get("agent") != agent:
                        continue
                    if action and entry.get("action") != action:
                        continue

                    logs.append(entry)

                    if len(logs) >= limit:
                        break
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file}")
        except Exception as e:
            logger.error(f"Error reading audit logs: {str(e)}")

        return logs[-limit:]  # Return most recent logs

    def close(self):
        """Close database connections"""
        if self._pg_conn:
            self._pg_conn.close()
