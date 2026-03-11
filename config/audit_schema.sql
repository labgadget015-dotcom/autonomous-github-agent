-- PostgreSQL Schema for Audit Logs
-- Creates tables for storing immutable audit trail

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    task_id VARCHAR(255) NOT NULL,
    agent VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    params JSONB,
    result JSONB,
    status VARCHAR(50) NOT NULL,
    rollback TEXT,
    
    -- Indexes for faster queries
    CONSTRAINT unique_task_action UNIQUE (task_id, agent, action, timestamp)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_task_id ON audit_logs(task_id);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_audit_agent_action ON audit_logs(agent, action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp_status ON audit_logs(timestamp DESC, status);

-- Add comments
COMMENT ON TABLE audit_logs IS 'Immutable audit trail for all agent actions';
COMMENT ON COLUMN audit_logs.timestamp IS 'When the action was performed';
COMMENT ON COLUMN audit_logs.task_id IS 'Unique identifier for the task';
COMMENT ON COLUMN audit_logs.agent IS 'Name of the agent that performed the action';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed';
COMMENT ON COLUMN audit_logs.params IS 'JSON parameters passed to the action';
COMMENT ON COLUMN audit_logs.result IS 'JSON result from the action';
COMMENT ON COLUMN audit_logs.status IS 'Status of the action (success, error, pending)';
COMMENT ON COLUMN audit_logs.rollback IS 'Instructions for rolling back this action';

-- Create view for recent actions
CREATE OR REPLACE VIEW recent_audit_logs AS
SELECT 
    id,
    timestamp,
    task_id,
    agent,
    action,
    status,
    rollback
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 1000;

-- Create view for error logs
CREATE OR REPLACE VIEW error_audit_logs AS
SELECT 
    id,
    timestamp,
    task_id,
    agent,
    action,
    params,
    result,
    rollback
FROM audit_logs
WHERE status = 'error'
ORDER BY timestamp DESC;

-- Function to archive old logs
CREATE OR REPLACE FUNCTION archive_old_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move old logs to archive table (or delete if archive not needed)
    WITH archived AS (
        DELETE FROM audit_logs
        WHERE timestamp < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL
        RETURNING *
    )
    SELECT COUNT(*) INTO archived_count FROM archived;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT ON audit_logs TO agent_user;
-- GRANT USAGE ON SEQUENCE audit_logs_id_seq TO agent_user;
