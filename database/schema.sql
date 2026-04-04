-- Echo Agent Proxy - Database Schema
-- Version: 1.0
-- Purpose: Track sessions, audit all actions, and store summaries

PRAGMA foreign_keys = ON;

-- 1. Sessions Table: All persistent PTY sessions (msfconsole, bash, etc.)
CREATE TABLE IF NOT EXISTS sessions (
    session_id          TEXT PRIMARY KEY,           -- e.g. "msf", "shell", "recon1"
    name                TEXT NOT NULL,               -- Human readable name
    tool_type           TEXT NOT NULL,               -- "msfconsole", "bash", "other"
    status              TEXT NOT NULL DEFAULT 'active', -- active, suspended, closed
    command             TEXT,                        -- Original launch command
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active         DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata            TEXT                         -- JSON for extra info (pid, etc.)
);

-- 2. Audit Log: Every action taken by Echo (full traceability)
CREATE TABLE IF NOT EXISTS audit_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id          TEXT,
    echo_action         TEXT NOT NULL,               -- What Echo decided to do
    command_sent        TEXT,                        -- Exact command sent to PTY
    checker_decision    TEXT,                        -- "approved", "rejected", "modified"
    status              TEXT NOT NULL,               -- "executed", "failed", "pending"
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 3. Summaries: Heartbeat summaries (keeps Echo's context clean)
CREATE TABLE IF NOT EXISTS summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL,
    timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary_type        TEXT NOT NULL,               -- "command_output", "heartbeat", "milestone"
    content             TEXT NOT NULL,               -- The actual summary
    raw_length          INTEGER,                     -- Original output length (for stats)
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 4. Session Memory: Long-term learnings per session
CREATE TABLE IF NOT EXISTS session_memory (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT,
    timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP,
    entry_type          TEXT NOT NULL,               -- "learning", "finding", "note"
    content             TEXT NOT NULL,
    importance          INTEGER DEFAULT 1,           -- 1-5
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_summaries_session ON summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_session ON session_memory(session_id);

-- View: Quick overview of active sessions with latest activity
CREATE VIEW IF NOT EXISTS active_sessions_view AS
SELECT 
    s.session_id,
    s.name,
    s.tool_type,
    s.status,
    s.last_active,
    COUNT(DISTINCT a.id) as action_count,
    MAX(a.timestamp) as last_action
FROM sessions s
LEFT JOIN audit_log a ON s.session_id = a.session_id
WHERE s.status = 'active'
GROUP BY s.session_id;
