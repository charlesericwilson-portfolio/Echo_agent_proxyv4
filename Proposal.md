# Project Echo: Session-Aware Local LLM Agent Proxy for Red Team Operations

**Project Proposal & Kick-off Document**
**Version:** 1.0
**Date:** April 04, 2026
**Author:** Charles
**Status:** Initial Planning & Architecture Phase

### 1. Project Overview

**Project Name:** Echo Agent Proxy (v3)

**Objective:**
Build a robust, modular, session-aware local LLM agent system that enables reliable interaction with stateful tools (especially Metasploit and shell sessions) while maintaining clean separation of concerns between reasoning, monitoring, validation, and execution.

The system will treat the LLM as the **brain** and build a proper **nervous system** around it using specialized components with their own focused roles and contexts.

### 2. Problem Statement

Current local LLM agents suffer from:
- Context bloat when dealing with long-running interactive tools
- Unreliable tool calling and syntax adherence
- Poor state management across parallel sessions
- Lack of separation between high-level reasoning and low-level execution/monitoring
- Difficulty logging and auditing agent actions

This project aims to solve these issues by creating a true multi-component agent architecture rather than a monolithic prompt-based system.

### 3. Project Goals

**Primary Goals:**
- Create a reliable persistent session system supporting multiple parallel tools (msfconsole, bash, etc.)
- Implement a heartbeat monitor that automatically summarizes session output
- Add a tool-call validator/checker as a second set of eyes before execution
- Use a structured database for session tracking, logging, and state management
- Maintain clean, auditable logs of all agent actions

**Secondary Goals:**
- Design the system to be easily portable to Rust in the future
- Produce high-quality documentation and artifacts suitable for a capstone project
- Create a foundation that can be extended to support any tool (not just msfconsole and bash)

### 4. High-Level Architecture

The system will follow a **true multi-agent orchestration** model with clear separation of concerns:

- **Echo (Main Reasoning Agent)**
  - Qwen2.5-Coder-14B-Instruct (or future upgrade)
  - Responsible for high-level planning and decision making
  - Receives summarized session data only

- **Heartbeat Monitor**
  - Small lightweight model (1B–3B)
  - Continuously monitors PTY session output
  - Generates structured summaries at task completion points
  - Routes summarized data back to Echo

- **Tool Call Checker / Router**
  - Small-to-medium coder model
  - Validates Echo’s intended commands
  - Routes to the correct execution path (JSON tool vs. session tool)
  - Enforces safety rules and one-command-per-turn discipline

- **Orchestrator + Database Layer**
  - Central service managing sessions, state, and communication
  - SQLite (initially) → potentially PostgreSQL later
  - Tracks all active sessions, their state, and full audit log

- **Execution Backend**
  - PTY-based session manager (existing raw_proxy.py foundation)
  - Supports multiple parallel persistent sessions

### 5. Development Methodology

**Recommended Approach: Hybrid Waterfall + Iterative**

- **Phase 1–3**: Waterfall-style (clear architecture, requirements, and design first)
- **Phase 4+**: Iterative development with frequent working prototypes

This gives us strong documentation and structure (important for capstone and future hiring) while still allowing flexibility once core components are defined.

### 6. Project Phases

1. **Planning & Architecture** (Current)
   - Finalize component responsibilities and interfaces
   - Design database schema
   - Define message formats between components

2. **Core Infrastructure**
   - Build Orchestrator + Database layer
   - Improve PTY session manager (auto-creation, better output handling)

3. **Component Development**
   - Heartbeat Monitor
   - Tool Call Checker
   - Updated Echo system prompts

4. **Integration & Testing**
   - Full end-to-end testing with parallel msfconsole + bash sessions
   - Safety and reliability testing

5. **Documentation & Polish**
   - Comprehensive project documentation
   - Capstoneready artifacts (diagrams, results, lessons learned)

6. **Future Extension (Rust Rewrite)**
   - Port critical components to Rust for better performance

### 7. Success Criteria

- Echo can reliably manage multiple parallel sessions (msfconsole + bash) with minimal human intervention
- Heartbeat monitor correctly summarizes output and reduces Echo’s context load
- Tool Call Checker catches at least 80% of malformed or dangerous commands
- All actions are logged in a queryable database
- System demonstrates clear separation of concerns

### 8. Risks & Mitigation

- Model reliability on custom syntax → Addressed with targeted synthetic data generation
- Increased system complexity → Start with minimal viable integration between components
- Performance overhead → Monitor resource usage; optimize later with Rust

### 9. Next Immediate Steps (Week 1)

1. Finalize and approve this architecture
2. Design the database schema for sessions and audit log
3. Update the PTY session manager with improved auto-creation and output handling
4. Create system prompts for Echo, Heartbeat, and Checker
5. Set up proper project folder structure with documentation

---

**Approval / Next Meeting Agenda:**
- Review and refine architecture
- Decide on initial database technology (SQLite vs PostgreSQL)
- Agree on communication protocol between components

This project has strong potential to become a standout capstone and a portfolio piece that demonstrates real systems thinking in local AI agent development.

Prepared for discussion.
