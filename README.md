# Echo Agent Proxy

**A Session-Aware, Multi-Component Local LLM Agent Framework for Red Team Operations**

Built by Charles | Assisted by Grok (xAI)

---

## Overview

Echo is a modular, local-first LLM agent system designed for reliable interaction with long-running interactive tools (especially Metasploit and shell sessions).

Instead of cramming everything into one giant prompt, Echo uses a true **"nervous system"** architecture:

- **Echo** — The reasoning brain (Qwen2.5-Coder-14B)
- **Heartbeat** — Lightweight monitor that summarizes session output
- **Tool Call Checker** — Second set of eyes that validates and routes commands
- **Orchestrator + Database** — Central state management and audit logging

This separation keeps the main model focused, reduces context bloat, and enables reliable parallel sessions.

### Key Features
- Native persistent PTY sessions (msfconsole, bash, etc.)
- Automatic output summarization via dedicated Heartbeat model
- Tool call validation and safety gates
- Structured SQLite database for sessions and full audit trail
- Clean separation of concerns (reasoning vs monitoring vs validation)
- Designed for easy adaptation to other workflows via LoRA

---

## Project Status

**Current Phase:** Week 1 – Foundation & Architecture  
**Goal:** Capstone-ready local red team agent by mid-July 2026

See `docs/PROJECT_PROPOSAL.md` and `docs/TIMELINE.md` for full details.

---

## Architecture
