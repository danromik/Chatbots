#!/usr/bin/env python3
"""
Command-line chatbot: multiline prompt (submit with Ctrl-S, abort with Ctrl-C),
sends to OpenAI API and prints timing, token usage, and response.
"""

import os
import sys
import time

# Load .env before using openai so API key is available
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI


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
        print("Enter your prompt (multiline). Submit with an empty line.")
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
        print("Enter your prompt (multiline). Submit with Ctrl-S, abort with Ctrl-C.")
        print()
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
    try:
        prompt = read_multiline_prompt()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)

    if not prompt.strip():
        print("Empty prompt. Exiting.")
        sys.exit(0)

    print("Submitting prompt...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Add it to a .env file in this project.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.perf_counter() - start
    usage = response.usage
    total_tokens = usage.total_tokens if usage else 0

    print()
    print(f"[ {elapsed:.2f}s, {total_tokens} tokens ]")
    print()
    content = response.choices[0].message.content
    if content:
        print(content)


if __name__ == "__main__":
    main()
