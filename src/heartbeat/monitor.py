#!/usr/bin/env python3
"""
Echo Agent Proxy - Heartbeat Monitor v1.5
Continuous polling until terminal is closed
"""

import asyncio
import sqlite3
import re
import requests
from pathlib import Path
from collections import defaultdict

from src.pty_backend.session_manager import active_sessions

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "echo.db"

SUMMARIZER_URL = "http://localhost:8082/v1/chat/completions"

class HeartbeatMonitor:
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.running = False
        self.last_output = defaultdict(str)  # Track last seen output per session

    async def start(self):
        self.running = True
        print("❤️ Heartbeat Monitor v1.5 - Continuous polling forever")

        while self.running:
            await self.check_sessions()
            await asyncio.sleep(self.interval)

    async def check_sessions(self):
        """Poll every session forever. Only summarize when new output + completion marker"""
        for session_id, session in list(active_sessions.items()):
            try:
                output = await session.get_output()
                clean = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output).strip()
                output_len = len(clean)

                if output_len == 0:
                    continue

                # Debug
                print(f"[Heartbeat] Checked '{session_id}' - {output_len} chars | Preview: {clean[:100]}...")

                # Only act if we see NEW output
                if clean != self.last_output[session_id]:
                    self.last_output[session_id] = clean

                    completion_markers = ["$", "#", "msf6 >", "Nmap done", "scan report", "Host is up", "ports scanned"]
                    if any(marker in clean for marker in completion_markers):
                        print(f"[Heartbeat] → Completion detected for '{session_id}' - Summarizing")
                        asyncio.create_task(self.safe_summarize(session_id, output))
                    else:
                        print(f"[Heartbeat] → New output but not complete yet for '{session_id}'")
                else:
                    print(f"[Heartbeat] → No new output for '{session_id}' - continuing to poll")

            except Exception as e:
                print(f"[Heartbeat] Error checking {session_id}: {e}")

    async def safe_summarize(self, session_id: str, raw_output: str):
        try:
            async with asyncio.timeout(10):
                clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', raw_output)

                prompt = f"""You are a precise red team summarizer.

Summarize the following terminal output from session '{session_id}' in maximum 4 short bullet points.

Focus ONLY on:
- Open ports and services
- Host information
- Scan completion status
- Any notable findings

Ignore shell prompts and noise.

Raw output:
{clean_output[-1800:]}"""

                payload = {
                    "model": "Summarizer-3.1B-Q4_K_M.gguf",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 180,
                    "stream": False
                }

                resp = requests.post(SUMMARIZER_URL, json=payload, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"] if "choices" in data else ""

                summary = str(content).strip()
                if not summary or len(summary) < 10:
                    summary = "No significant new output."

                # Save to DB
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO summaries (session_id, summary_type, content, raw_length)
                    VALUES (?, 'heartbeat_summary', ?, ?)
                """, (session_id, summary, len(raw_output)))
                conn.commit()
                conn.close()

                print(f"[Heartbeat] ✓ Summary saved for '{session_id}'")

                # Feed back to model as tool message (simple print for now)
                feedback = f"[TOOL RESULT from {session_id}]: {summary}"
                print(f"{Fore.CYAN}{feedback}{Style.RESET_ALL}")

        except Exception as e:
            print(f"[Heartbeat] ❌ Summarization failed for '{session_id}': {e}")

    def stop(self):
        self.running = False


heartbeat = HeartbeatMonitor()

async def start_heartbeat():
    await heartbeat.start()
