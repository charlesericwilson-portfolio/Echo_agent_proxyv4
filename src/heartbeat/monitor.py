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
        """Clean and summarize output, then save to DB"""
        # Simple aggressive cleaning first
        cleaned = self.clean_output(raw_output)

        # Call summarizer (your small model on port 8082)
        summary = await self.call_summarizer(cleaned)

        # Save to database
        self.conn.execute(
            "INSERT INTO summaries (session_id, summary_type, content) VALUES (?, ?, ?)",
            (session_id, "command_output", summary)
        )
        self.conn.commit()

        return summary

    def clean_output(self, output: str) -> str:
        """Remove common noise"""
        lines = output.splitlines()
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(("eric@", "root@", "msf >", "msf exploit")):
                continue
            if "echo '===ECHO_" in line:
                continue
            cleaned.append(line)
        return "\n".join(cleaned[-100:])   # keep last 100 lines max

    async def call_summarizer(self, text: str) -> str:
        """Call your small summarizer model on port 8082"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8082/v1/chat/completions",
                    json={
                        "model": "Summarizer-3.1B-Q4_K_M.gguf",
                        "messages": [
                            {"role": "system", "content": "You are a high-signal cleaner. Remove noise and return only the important technical output. Be concise."},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 400
                    },
                    timeout=30.0
                )
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[Summarizer error: {str(e)}]\n\n{text[:500]}"   # fallback

# Global instance
monitor = HeartbeatMonitor()

async def get_summary(session_id: str, raw_output: str):
    return await monitor.summarize_and_save(session_id, raw_output)
