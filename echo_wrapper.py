#!/usr/bin/env python3
"""
Echo Wrapper - Clean Version
Just talks to orchestrator, no direct summarizer logic
"""

import re
import requests
from colorama import init, Fore, Style

init(autoreset=True)

ORCHESTRATOR_URL = "http://localhost:8000/tool"
LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = """You are Echo, a professional red team agent.

Use this exact format for all commands:
SESSION:NAME command

Rules:
- SESSION:NAME should auto create a bash -i terminal.
- Then send commands: SESSION:NAME actual_command
- After sending a command, you will receive TOOL OUTPUT (already summarized).
- Be methodical and stateful."""

class EchoWrapper:
    def __init__(self):
        self.session_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        print(f"{Fore.CYAN}Echo Wrapper - Clean Version{Style.RESET_ALL}")

    def send_to_echo(self, user_input: str):
        try:
            payload = {
                "model": "custom_echov2.Q5_K_M.gguf",
                "messages": self.session_history + [{"role": "user", "content": user_input}],
                "temperature": 0.3,
                "max_tokens": 1024,
                "stream": False
            }
            resp = requests.post(LLAMA_SERVER_URL, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"{Fore.RED}Echo error: {e}{Style.RESET_ALL}")
            return f"Error: {e}"

    def call_orchestrator(self, action: str, session_id: str, command: str = None):
        try:
            payload = {"action": action, "session_id": session_id, "command": command}
            resp = requests.post(ORCHESTRATOR_URL, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"{Fore.RED}Orchestrator error: {e}{Style.RESET_ALL}")
            return {"error": str(e)}

    def process_echo_output(self, output: str):
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if not line.startswith("SESSION:"):
                continue

            try:
                match = re.match(r"SESSION:(\S+)\s+(.*)", line)
                if not match:
                    continue

                session_id = match.group(1)
                command = match.group(2).strip()

                print(f"{Fore.MAGENTA}→ Detected: SESSION:{session_id} {command}{Style.RESET_ALL}")

                action = "create_session" if any(x in command.lower() for x in ["bash", "sh", "msfconsole"]) else "send_command"

                result = self.call_orchestrator(action, session_id, command)

                if result and "output" in result:
                    tool_message = f"[TOOL OUTPUT from {session_id}]:\n{result['output']}"
                    print(f"{Fore.CYAN}{tool_message}{Style.RESET_ALL}")
                    self.session_history.append({"role": "tool", "content": tool_message})

            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

    def chat_loop(self):
        print(f"{Fore.CYAN}Chat started. Type 'exit' to quit.{Style.RESET_ALL}\n")

        while True:
            try:
                user_input = input(f"{Fore.WHITE}You: {Style.RESET_ALL}")
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{Fore.YELLOW}Goodbye.{Style.RESET_ALL}")
                    break

                print(f"{Fore.BLUE}Echo thinking...{Style.RESET_ALL}")
                echo_response = self.send_to_echo(user_input)

                print(f"{Fore.GREEN}Echo:{Style.RESET_ALL}")
                print(echo_response)

                self.process_echo_output(echo_response)

                self.session_history.append({"role": "user", "content": user_input})
                self.session_history.append({"role": "assistant", "content": echo_response})

                if len(self.session_history) > 30:
                    self.session_history = self.session_history[-30:]

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    wrapper = EchoWrapper()
    wrapper.chat_loop()
