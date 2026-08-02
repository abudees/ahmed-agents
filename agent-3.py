#!/usr/bin/env python3
"""Data-processing agent built on the Claude API.

Agent loop:
  1. Read  — load a CSV or JSON file into a list of row dicts.
  2. Ask   — send the rows plus a natural-language instruction to Claude and
             ask it to filter/sort/aggregate/transform them.
  3. Write — parse Claude's JSON response and print + save the result.

Usage:
  python3 agent-3.py <input.csv|input.json> <instruction...> [-o output.json]

Example:
  python3 agent-3.py sales.csv "sort by revenue descending and keep only rows over $1000"
  python3 agent-3.py sales.csv "group by region and sum revenue" -o by_region.json
"""

import csv
import json
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-5"
MAX_TOKENS = 16000


def read_data(path: Path) -> list:
    """Load a CSV or JSON file into a list of dicts."""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        return data

    raise ValueError(f"Unsupported file type: {path.suffix} (expected .csv or .json)")


def ask_claude(client: anthropic.Anthropic, rows: list, instruction: str) -> list:
    """Send the data + instruction to Claude and return the processed rows."""
    prompt = f"""Here is a dataset as a JSON array of row objects:

{json.dumps(rows, indent=2)}

Task: {instruction}

Apply the requested filtering, sorting, aggregation, or transformation and
return ONLY the resulting data as a JSON array of objects — no prose, no
markdown code fences, no explanation. If the task produces aggregate values
(e.g. group totals), each group should be one object in the array."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return parse_json_array(text)


def parse_json_array(text: str) -> list:
    """Parse a JSON array out of Claude's response, tolerating code fences."""
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude did not return valid JSON: {e}\n---\n{text}") from e

    if isinstance(result, dict):
        result = [result]
    return result


def write_output(rows: list, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def main() -> int:
    args = sys.argv[1:]

    output_path = None
    if "-o" in args:
        i = args.index("-o")
        output_path = Path(args[i + 1])
        del args[i : i + 2]
    elif "--output" in args:
        i = args.index("--output")
        output_path = Path(args[i + 1])
        del args[i : i + 2]

    if len(args) < 2:
        print(
            "Usage: python3 agent-3.py <input.csv|input.json> <instruction...> [-o output.json]",
            file=sys.stderr,
        )
        return 1

    input_path = Path(args[0])
    instruction = " ".join(args[1:]).strip()

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_processed.json")

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        rows = read_data(input_path)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"Failed to read {input_path}: {e}", file=sys.stderr)
        return 1

    print(f"[read {len(rows)} row(s) from {input_path}]", file=sys.stderr)
    print(f"[asking Claude: {instruction!r}]", file=sys.stderr)

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        print(f"Failed to initialize Claude client: {e}", file=sys.stderr)
        return 1

    try:
        result = ask_claude(client, rows, instruction)
    except anthropic.AuthenticationError:
        print(
            "Authentication failed — set the ANTHROPIC_API_KEY environment "
            "variable with a valid API key.",
            file=sys.stderr,
        )
        return 1
    except anthropic.RateLimitError:
        print("Rate limited by the Claude API — please try again shortly.", file=sys.stderr)
        return 1
    except anthropic.APIConnectionError:
        print("Could not connect to the Claude API — check your network connection.", file=sys.stderr)
        return 1
    except anthropic.APIStatusError as e:
        print(f"Claude API error ({e.status_code}): {e.message}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Failed to parse Claude's response: {e}", file=sys.stderr)
        return 1

    write_output(result, output_path)
    print(f"[wrote {len(result)} row(s) to {output_path}]", file=sys.stderr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
