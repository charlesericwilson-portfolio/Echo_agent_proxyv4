#!/usr/bin/env python3
"""
Echo Agent Proxy - Heartbeat Monitor v1.2
Fixed indentation + robust summarization
"""

import asyncio
import sqlite3
import re
import json  # Added for safety
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
        print("❤️ Heartbeat Monitor v1.2 - Clean version with debug logging")

        while self.running:
            await self.check_sessions()
            await asyncio.sleep(self.interval)

    async def check_sessions(self):
        """Check all active sessions for new output - tuned for stability"""
        for session_id, session in list(active_sessions.items()):
            try:
                output = await session.get_output()

                clean_for_check = output.strip()
                output_len = len(clean_for_check)

                # Debug - keep for now
                if output_len > 0:
                    print(f"[Heartbeat] Checked '{session_id}' - {output_len} chars")

                # Trigger on reasonable output (bash prompts + command results usually ~100-400 chars)
                if output and output_len > 40:
                    print(f"[Heartbeat] → Triggering summarization for '{session_id}' ({output_len} chars)")
                    asyncio.create_task(self.safe_summarize(session_id, output))
                elif output_len > 0:
                    print(f"[Heartbeat] → Output too short ({output_len} chars)")

            except Exception as e:
                print(f"[Heartbeat] Error checking {session_id}: {e}")

    async def safe_summarize(self, session_id: str, raw_output: str):
        """Robust summarization using the actual running model"""
        try:
            async with asyncio.timeout(10):
                clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', raw_output)

                prompt = f"""You are a concise red team output summarizer for session '{session_id}'.

Focus ONLY on key information:
- Username, hostname, current directory
- Commands that were executed
- Results or output from those commands
- Any errors or interesting findings

Be brief and factual. One short paragraph maximum. Ignore shell prompts and noise.

Output:
{clean_output[-1800:]}"""

                payload = {
                    "model": "Summarizer-3.1B-Q4_K_M.gguf",   # Use your actual model name
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 220,
                    "stream": False
                }

                resp = requests.post(SUMMARIZER_URL, json=payload, timeout=10)
                resp.raise_for_status()

                data = resp.json()
                content = ""
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    content = choice.get("message", {}).get("content") or choice.get("text") or str(choice)

                summary = str(content).strip()
                if not summary or len(summary) < 10:
                    summary = "Output received but summarizer returned empty result."

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO summaries (session_id, summary_type, content, raw_length)
                    VALUES (?, 'heartbeat_summary', ?, ?)
                """, (session_id, summary, len(raw_output)))
                conn.commit()
                conn.close()

                print(f"[Heartbeat] ✓ Summary saved for '{session_id}' ({len(summary)} chars)")

        except Exception as e:
            print(f"[Heartbeat] ❌ Summarization failed for '{session_id}': {type(e).__name__} - {e}")
            # Optional fallback
            fallback = f"Raw output captured ({len(raw_output)} chars). Preview: {raw_output[:250].replace(chr(10), ' ')}..."
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO summaries (session_id, summary_type, content, raw_length)
                VALUES (?, 'heartbeat_fallback', ?, ?)
            """, (session_id, fallback, len(raw_output)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Heartbeat] ❌ Unexpected error summarizing '{session_id}': {e}")

    def stop(self):
        self.running = False


# Global instance
heartbeat = HeartbeatMonitor()

async def start_heartbeat():
    await heartbeat.start()
