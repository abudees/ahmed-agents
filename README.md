# Ahmed Agents - Agentic PM Portfolio

Building AI agents and agentic systems to demonstrate agentic PM competencies.

## Agents

| Agent | Purpose | Demonstrates |
|-------|---------|--------------|
| Agent #1 | Hello World | Basic Claude API integration |
| Agent #2 | Web Search | Tool calling patterns |
| Agent #3 | Data Processor | Multi-step reasoning |
| Agent #4 | Multi-Step Task | Planning & execution |
| Agent #5 | Claude Code Native | Session management & state |

## Setup

### 1. Get API Key

Go to: https://console.anthropic.com/api-keys

Create a new API key.

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-YOUR-KEY-HERE"
```

Replace `sk-ant-YOUR-KEY-HERE` with your actual key (keep it secret!).

### 3. Run an Agent

```bash
python3 agent-1.py "Hello, what is an AI agent?"
```

Or any query:
```bash
python3 agent-2.py "latest AI developments"
python3 agent-3.py "process this data"
```

## Requirements

- Python 3.12+
- Anthropic API key with credits
- `anthropic` library

```bash
pip3 install anthropic
```

## Portfolio Goal

Demonstrating core agentic patterns:
- ✅ Tool use & function calling
- ✅ Multi-step reasoning
- ✅ State management
- ✅ Agent orchestration

## Next Steps

- Digital Twin agent (deployed)
- Multi-Agent Orchestrator
- YazSeed Logistics Capstone (real business case)

---

**Built: Jul 2026 | Product School AI Builder Week**