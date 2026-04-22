import asyncio
import json
from datetime import datetime
import sqlite3

class HeartbeatMonitor:
    def __init__(self, db_path="database/echo.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                summary_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    async def summarize_and_save(self, session_id: str, raw_output: str):
        cleaned = self.clean_output(raw_output)
        summary = await self.call_summarizer(cleaned)   # ← real summarizer call is back on

        self.conn.execute(
            "INSERT INTO summaries (session_id, summary_type, content) VALUES (?, ?, ?)",
            (session_id, "command_output", summary)
        )
        self.conn.commit()
        return summary

    def clean_output(self, output: str) -> str:
        lines = output.splitlines()
        cleaned = [line for line in lines if "===ECHO_" not in line]
        return "\n".join(cleaned[-100:])

    async def call_summarizer(self, text: str) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8082/v1/chat/completions",
                    json={
                        "model": "Summarizer-3.1B-Q4_K_M.gguf",
                        "messages": [
                            {"role": "system", "content": "You are a professional summarizer. Always give IP when present. Never hallucinate output. Do not give explainations."},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1028,
                        "cache_prompt": False
                    },
                    timeout=25.0
                )
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # Safe fallback — return the real tool output instead of hallucinating
            return text[:600] if text else "No output"

# Global instance
monitor = HeartbeatMonitor()

async def get_summary(session_id: str, raw_output: str):
    return await monitor.summarize_and_save(session_id, raw_output)
