# Echo Agent Proxy

**A Session-Aware, Multi-Component Local LLM Agent Framework for Red Team Operations**

Built with ❤️ by Charles | Guided by Grok (xAI)

---

## Overview

Echo is a modular, local-first LLM agent system designed for reliable interaction with long-running interactive tools such as Metasploit (`msfconsole`) and shell sessions.

Instead of forcing everything into a single prompt, Echo uses a true **nervous system** architecture:

- **Echo** — Main reasoning brain (Qwen2.5-Coder-14B)
- **Heartbeat** — Dedicated lightweight monitor that summarizes session output
- **Tool Call Checker** — Second set of eyes that validates and routes commands
- **Orchestrator + Database** — Central coordination and persistent state

This design reduces context bloat, improves reliability, and makes the system much more maintainable.

### Key Features
- Native persistent PTY sessions with parallel support
- Automatic output summarization via Heartbeat model
- Tool call validation and safety gates
- Structured SQLite database for sessions and full audit logging
- Designed for easy adaptation to other workflows via LoRA

---

## Current Status

**Phase:** 1 — Foundation & Architecture  
**Started:** April 2026

See `docs/PROJECT_PROPOSAL.md` and `docs/TIMELINE.md` for full details.

---

## Project Structure
echo-agent-proxy/
├── docs/                    # Documentation
├── src/                     # Source code
│   ├── orchestrator/
│   ├── heartbeat/
│   ├── checker/
│   └── pty_backend/
├── database/                # SQLite schema
├── sessions/                # Active PTY sessions
├── logs/
├── architecture/            # Diagrams
├── tests/
├── progress_log.md
├── README.md
└── .gitignore

---

## Roadmap

See `docs/TIMELINE.md` for the detailed 12-week plan.

**Phase 1** (Current): Project setup, database schema, improved PTY backend  

---

## Acknowledgments

Special thanks to Grok (xAI) for the architecture guidance and continuous support.

---

**License:** MIT  
**Status:** In active development (April 2026)
