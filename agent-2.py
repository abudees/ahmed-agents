#!/usr/bin/env python3
"""Simple web-search-and-summarize agent built on the Claude API.

Flow:
  1. Take a user query (CLI arg or interactive prompt).
  2. Give Claude a `search_web` tool it can call to look up information.
  3. Execute the tool call locally (stubbed search results — swap in a real
     search API like Serper/Tavily/Bing by replacing the body of
     `search_web`) and hand the results back to Claude.
  4. Claude reads the results and returns a summary, which we print.
"""

import sys

import anthropic

MODEL = "claude-opus-5"
MAX_TOOL_ITERATIONS = 3

TOOLS = [
    {
        "name": "search_web",
        "description": (
            "Search the web for current information about a topic. Call this "
            "before answering any question that depends on facts, recent "
            "events, or information you are not confident about from memory."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
            },
            "required": ["query"],
        },
    }
]


def search_web(query: str) -> str:
    """Stub web search — replace with a real search API for production use.

    A real implementation would call something like the Serper, Tavily, or
    Bing Search API here and return the actual results. This stub returns
    plausible-looking placeholder results so the tool-calling flow can be
    demonstrated without requiring a search API key.
    """
    try:
        results = [
            {
                "title": f"Result 1 for '{query}'",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}-1",
                "snippet": f"An overview of {query}, covering the key background and context.",
            },
            {
                "title": f"Result 2 for '{query}'",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}-2",
                "snippet": f"Recent developments and details related to {query}.",
            },
            {
                "title": f"Result 3 for '{query}'",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}-3",
                "snippet": f"Frequently asked questions and expert opinions on {query}.",
            },
        ]
        lines = [f"- {r['title']} ({r['url']}): {r['snippet']}" for r in results]
        return "\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


def run_agent(client: anthropic.Anthropic, user_query: str) -> str:
    messages = [
        {
            "role": "user",
            "content": (
                f"Research the following and give me a concise summary: {user_query}"
            ),
        }
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "search_web":
                query = block.input.get("query", user_query)
                print(f"[searching web for: {query!r}]", file=sys.stderr)
                result = search_web(query)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    return "Sorry, I couldn't finish researching that in time — try a narrower query."


def main() -> int:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        try:
            query = input("Enter your query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo query provided.", file=sys.stderr)
            return 1

    if not query:
        print("No query provided.", file=sys.stderr)
        return 1

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        print(f"Failed to initialize Claude client: {e}", file=sys.stderr)
        return 1

    try:
        summary = run_agent(client, query)
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
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
