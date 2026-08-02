#!/usr/bin/env python3
"""
agent-5.py — a stateful conversational agent using Claude's Messages API.

The Claude API itself is stateless — it has no memory between calls. Memory
here is created entirely on our side: a conversation_history list grows with
every turn, and the *entire* list is resent on each call so Claude can see
everything said so far. Append user input -> call API -> append reply ->
repeat.

Usage:
    python agent-5.py            # interactive chat
    python agent-5.py --demo     # scripted demo showing memory across turns
"""

from __future__ import annotations

import sys
from typing import Dict, List

import anthropic

MODEL = "claude-opus-5"
SYSTEM_PROMPT = "You are a helpful, concise assistant."


def hr(char: str = "-", width: int = 70) -> None:
    print(char * width)


class Agent:
    """Wraps the Claude API with a growing conversation_history list."""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.conversation_history: List[Dict] = []

    def send(self, user_input: str) -> str:
        # 1. Add the user's message to history
        self.conversation_history.append({"role": "user", "content": user_input})

        # 2. Send the entire history so far — the API has no memory of its own
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history,
        )

        reply = next((b.text for b in response.content if b.type == "text"), "")

        # 3. Add Claude's reply to history so future turns can reference it
        self.conversation_history.append({"role": "assistant", "content": reply})

        return reply


def run_demo(agent: Agent) -> None:
    """Scripted exchanges showing the agent 'learning' from earlier turns."""
    turns = [
        "My name is Ahmed and my favorite language is Python.",
        "What's my name?",
        "What's my favorite programming language?",
        "Multiply the number of letters in my name by 3.",
    ]

    hr("=")
    print("DEMO: stateful memory across turns")
    hr("=")

    for turn in turns:
        print(f"\nYou: {turn}")
        reply = agent.send(turn)
        print(f"Claude: {reply}")
        print(f"  (history now holds {len(agent.conversation_history)} messages)")


def run_interactive(agent: Agent) -> None:
    print("agent-5 ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        reply = agent.send(user_input)
        print(f"Claude: {reply}\n")


def main() -> None:
    client = anthropic.Anthropic()
    agent = Agent(client)

    try:
        if "--demo" in sys.argv:
            run_demo(agent)
        else:
            run_interactive(agent)
    except anthropic.AuthenticationError:
        print("Authentication failed. Set ANTHROPIC_API_KEY or run `ant auth login`.")
        sys.exit(1)
    except anthropic.RateLimitError as e:
        print(f"Rate limited: {e}")
        sys.exit(1)
    except anthropic.APIConnectionError as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"API error ({e.status_code}): {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
