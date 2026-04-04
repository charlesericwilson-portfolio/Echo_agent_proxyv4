#!/usr/bin/env python3
"""
Echo Agent Proxy - Heartbeat Monitor v1.1
Non-blocking + timeout protection
"""

import asyncio
import sqlite3
import re
import time
import requests
from pathlib import Path

from src.pty_backend.session_manager import active_sessions

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "echo.db"

SUMMARIZER_URL = "http://localhost:8082/v1/chat/completions"

class HeartbeatMonitor:
    def __init__(self, interval: float = 3.0):
        self.interval = interval
        self.running = False

    async def start(self):
        self.running = True
        print("❤️ Heartbeat Monitor v1.1 - Stable version with timeouts")

        while self.running:
            await self.check_sessions()
            await asyncio.sleep(self.interval)

    async def check_sessions(self):
        for session_id, session in list(active_sessions.items()):
            try:
                output = session.get_output()
                if output and len(output.strip()) > 60:
                    # Run summarization in a separate task with timeout
                    asyncio.create_task(self.safe_summarize(session_id, output))
            except Exception as e:
                print(f"[Heartbeat] Error checking {session_id}: {e}")

    async def safe_summarize(self, session_id: str, raw_output: str):
        """Safe summarization with timeout"""
        try:
            async with asyncio.timeout(8):   # 8 second timeout
                clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', raw_output)

                prompt = f"""Summarize this terminal output from session '{session_id}' concisely.
Focus only on key information.

Output:
{clean_output[-1800:]}"""

                payload = {
                    "model": "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 280
                }

                resp = requests.post(SUMMARIZER_URL, json=payload, timeout=8)
                summary = resp.json()["choices"][0]["message"]["content"].strip()

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO summaries (session_id, summary_type, content, raw_length)
                    VALUES (?, 'heartbeat_summary', ?, ?)
                """, (session_id, summary, len(raw_output)))
                conn.commit()
                conn.close()

                print(f"[Heartbeat] ✓ Summary saved for '{session_id}'")

        except asyncio.TimeoutError:
            print(f"[Heartbeat] Summarization timed out for '{session_id}'")
        except Exception as e:
            print(f"[Heartbeat] Summarization failed for '{session_id}': {e}")

    def stop(self):
        self.running = False

heartbeat = HeartbeatMonitor()

async def start_heartbeat():
    await heartbeat.start()
