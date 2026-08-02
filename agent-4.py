#!/usr/bin/env python3
"""
agent-4.py — a small planning agent.

Takes a complex task, asks Claude to break it into an ordered list of
subtasks, executes each subtask sequentially (feeding prior results in as
context), then asks Claude to synthesize everything into one final plan.

Usage:
    python agent-4.py "Plan a trip to Tokyo"
    python agent-4.py                      # uses a built-in example task
"""

from __future__ import annotations

import sys
from typing import List

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5"


# ---------------------------------------------------------------------------
# Structured output schema for the decomposition step
# ---------------------------------------------------------------------------

class Subtask(BaseModel):
    title: str
    description: str


class Plan(BaseModel):
    reasoning: str
    steps: List[Subtask]


def hr(char: str = "-", width: int = 70) -> None:
    print(char * width)


def print_thinking(response) -> None:
    """Print any thinking blocks Claude produced, so the reasoning is visible."""
    for block in response.content:
        if block.type == "thinking" and block.thinking:
            print("  [reasoning] " + block.thinking.replace("\n", "\n  [reasoning] "))


# ---------------------------------------------------------------------------
# Step 1: decompose the task into subtasks
# ---------------------------------------------------------------------------

def decompose_task(client: anthropic.Anthropic, task: str) -> Plan:
    print(f"\n>>> Decomposing task: {task!r}\n")

    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "high"},
        system=(
            "You are a planning agent. Given a complex task, break it into "
            "a small ordered sequence of concrete, actionable subtasks that "
            "together accomplish it. Each subtask should be independently "
            "executable given the results of the ones before it. Keep the "
            "list focused — typically 3 to 7 steps."
        ),
        messages=[{"role": "user", "content": task}],
        output_format=Plan,
    )

    print_thinking(response)

    plan = response.parsed_output
    print(f"\n  Overall approach: {plan.reasoning}\n")
    print("  Planned steps:")
    for i, step in enumerate(plan.steps, 1):
        print(f"    {i}. {step.title} — {step.description}")

    return plan


# ---------------------------------------------------------------------------
# Step 2: execute each subtask sequentially, carrying prior results forward
# ---------------------------------------------------------------------------

def execute_step(
    client: anthropic.Anthropic,
    task: str,
    plan: Plan,
    step_index: int,
    prior_results: List[str],
) -> str:
    step = plan.steps[step_index]
    print(f"\n>>> Executing step {step_index + 1}/{len(plan.steps)}: {step.title}\n")

    context_parts = [f"Overall task: {task}", f"Full plan:"]
    for i, s in enumerate(plan.steps, 1):
        context_parts.append(f"  {i}. {s.title} — {s.description}")

    if prior_results:
        context_parts.append("\nResults so far:")
        for i, result in enumerate(prior_results, 1):
            context_parts.append(f"--- Result of step {i} ({plan.steps[i - 1].title}) ---")
            context_parts.append(result)

    context_parts.append(
        f"\nNow complete step {step_index + 1}: {step.title} — {step.description}\n"
        "Produce a focused, concrete result for this step only. Build on the "
        "results above where relevant; do not repeat work already done."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "medium"},
        system="You are a diligent assistant executing one step of a larger plan.",
        messages=[{"role": "user", "content": "\n".join(context_parts)}],
    )

    if response.stop_reason == "refusal":
        result_text = f"[Step declined: {getattr(response.stop_details, 'explanation', 'no explanation given')}]"
    else:
        print_thinking(response)
        result_text = next((b.text for b in response.content if b.type == "text"), "")

    print(f"\n  Result: {result_text[:400]}{'...' if len(result_text) > 400 else ''}")
    return result_text


# ---------------------------------------------------------------------------
# Step 3: combine all step results into one final plan
# ---------------------------------------------------------------------------

def combine_results(
    client: anthropic.Anthropic, task: str, plan: Plan, results: List[str]
) -> str:
    print("\n>>> Combining results into final plan\n")

    parts = [f"Original task: {task}\n"]
    for i, (step, result) in enumerate(zip(plan.steps, results), 1):
        parts.append(f"Step {i}: {step.title}")
        parts.append(result)
        parts.append("")

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "high"},
        system=(
            "You are a planning agent. You are given the results of each "
            "step of a plan, produced sequentially. Synthesize them into a "
            "single, coherent, well-organized final deliverable that "
            "directly answers the original task. Do not just concatenate "
            "the step results — integrate them."
        ),
        messages=[{"role": "user", "content": "\n".join(parts)}],
    )

    print_thinking(response)
    return next((b.text for b in response.content if b.type == "text"), "")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_agent(task: str) -> str:
    client = anthropic.Anthropic()

    hr("=")
    print(f"TASK: {task}")
    hr("=")

    plan = decompose_task(client, task)

    results: List[str] = []
    for i in range(len(plan.steps)):
        result = execute_step(client, task, plan, i, results)
        results.append(result)

    final_plan = combine_results(client, task, plan, results)

    hr("=")
    print("FINAL PLAN")
    hr("=")
    print(final_plan)

    return final_plan


def main() -> None:
    task = " ".join(sys.argv[1:]).strip() or "Plan a trip to Tokyo"

    try:
        run_agent(task)
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
