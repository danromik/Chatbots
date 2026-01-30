#!/usr/bin/env python3
"""
Command-line chatbot: multiline prompt (submit with Ctrl-S, abort with Ctrl-C),
sends to OpenAI API or a local OpenAI-compatible LLM; prints timing, token usage, and response.
"""

import argparse
import os
import sys
import time

# Load .env before using openai so API key is available
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from rich.console import Console

console = Console()

DEFAULT_SYSTEM_PROMPT = "You are a helpful math assistant."
LOCAL_LLM_BASE_URL = "http://localhost:1234/v1"


def load_system_prompt() -> str:
    """Load system prompt from prompts.txt in the project directory, or use default."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(project_dir, "prompts.txt")
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content
    except FileNotFoundError:
        pass
    return DEFAULT_SYSTEM_PROMPT


def read_multiline_prompt() -> str:
    """Read multiline input until Ctrl-S (submit) or Ctrl-C (abort)."""
    if not sys.stdin.isatty():
        # Piped input: read until EOF
        return sys.stdin.read().strip()

    try:
        import termios
        import tty
    except ImportError:
        # Non-Unix (e.g. Windows): fallback to "empty line to submit"
        console.print("I am Alfred, your mathematical assistant.", style="bold")
        console.print("Enter your question (multiline). Submit with an empty line.", style="dim")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            lines.append(line)
        return "\n".join(lines)

    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    lines = []
    current = []

    try:
        console.print("I am Alfred, your mathematical assistant.", style="bold")
        console.print("Enter your question (multiline). Submit with Ctrl-S, abort with Ctrl-C.", style="dim")
        console.print()
        sys.stdout.flush()
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":  # Ctrl-C
                raise KeyboardInterrupt
            if ch == "\x13":  # Ctrl-S
                break
            if ch in ("\r", "\n"):
                lines.append("".join(current))
                current = []
                sys.stdout.write("\r\n")
                sys.stdout.flush()
            elif ch in ("\x7f", "\x08"):  # Backspace (DEL or BS)
                if current:
                    current.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            else:
                current.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()

        lines.append("".join(current))
        return "\n".join(lines).strip()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chatbot: send prompts to OpenAI or a local LLM.")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local LLM at localhost:1234 (OpenAI-compatible API) instead of OpenAI.",
    )
    args = parser.parse_args()

    try:
        prompt = read_multiline_prompt()
    except KeyboardInterrupt:
        console.print("\nAborted.", style="dim")
        sys.exit(0)

    if not prompt.strip():
        console.print("Empty prompt. Exiting.", style="dim")
        sys.exit(0)

    console.print("\n[Submitting prompt...]", style="bold cyan")
    if args.local:
        client = OpenAI(base_url=LOCAL_LLM_BASE_URL, api_key="not needed")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("Error: OPENAI_API_KEY not set. Add it to a .env file in this project.", style="bold red")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
    system_prompt = load_system_prompt()

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as e:
        console.print(f"API error: {e}", style="bold red")
        sys.exit(1)

    elapsed = time.perf_counter() - start
    usage = response.usage
    total_tokens = usage.total_tokens if usage else 0

    console.print()
    console.print(f"[ {elapsed:.2f}s, {total_tokens} tokens ]", style="cyan")
    console.print("LLM response:", style="bold")
    console.print()
    content = response.choices[0].message.content
    if content:
        console.print(content, style="blue")


if __name__ == "__main__":
    main()
