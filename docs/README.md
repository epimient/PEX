# PEX Documentation

**PEX** — Programs intention, not implementation.

## 📚 Documentation Index

### Getting Started
- [Introduction](#introduction) — What is PEX?
- [Quick Start](#quick-start) — Your first PEX program
- [Installation](#installation) — Requirements and setup

### Language Reference
- [Syntax Guide](syntax.md) — Complete syntax reference
- [Blocks & Structures](structures.md) — task, agent, pipeline, tool, model
- [Data Types](types.md) — Variables, records, entities

### Architecture
- [How PEX Works](architecture.md) — Lexer, Parser, Planner, Runtime
- [Adapters](adapters.md) — LLM, Database, File integrations
- [Execution Model](execution.md) — From .pi to execution

### CLI Reference
- [Command Line Interface](cli.md) — All commands and flags

### Examples
- [Hello World](examples.md#hello-world)
- [Database Query](examples.md#database-query)
- [AI Pipeline](examples.md#ai-pipeline)
- [Multi-file Project](examples.md#multi-file-project)

---

## Introduction

PEX is a **cognitive programming language** designed for the age of artificial intelligence.

### Philosophy

For decades, programming languages were designed to control machines through precise, deterministic instructions. PEX was created for a new context: **collaborating with artificial intelligences**.

Instead of describing every step of an algorithm, in PEX the programmer describes:
- **Intentions** (`task`, `agent`, `pipeline`)
- **Context** (`memory`, `variables`, `context`)
- **Resources** (`tool`, `model`)
- **Data Structures** (`record`, `entity`)

### The Zen of PEX

1. **Intention over implementation** — Describe what, not how
2. **Clarity over complexity** — Readable code wins
3. **Structure over prompts** — Organized intelligence
4. **Describe the goal** — Let AI figure out the steps
5. **Intelligence is part of the runtime** — AI is built-in, not a library

---

## Quick Start

### Your First PEX Program

Create `hello.pi`:

```pex
task hello
   goal say hello to the world and introduce PEX
```

Run it:

```bash
python main.py run hello.pi
```

### A More Complete Example

```pex
project sales_analysis

# Models
model analyst
   provider openai
   name gpt-4

# Tools
tool sales_db
   provider sqlite
   source $SALES_DB_URL

# Tasks
task get_sales
   input sales_db
   sql """
       SELECT product, SUM(revenue) as total
       FROM sales
       GROUP BY product
       ORDER BY total DESC
   """
   output sales_data

task analyze_trends
   input sales_data
   model analyst
   goal identify top performing products and suggest improvements
   output insights

# Pipeline
pipeline monthly_report
   step get_sales
   step analyze_trends
```

---

## Installation

### Requirements

- Python 3.10+
- Optional: `openai` package for OpenAI integration
- Optional: `psycopg2-binary` for PostgreSQL
- Optional: `requests` for Ollama (local LLM)

### Setup

```bash
# Clone or download PEX
cd PEX

# (Optional) Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# (Optional) Install dependencies
pip install openai psycopg2-binary requests
```

### Environment Variables

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4
SALES_DB_URL=postgres://localhost:5432/sales
DATABASE_URL=sqlite://./data.db
```

---

## Documentation Navigation

| Document | Description |
|----------|-------------|
| [syntax.md](syntax.md) | Complete language syntax |
| [structures.md](structures.md) | All block types explained |
| [architecture.md](architecture.md) | How the interpreter works |
| [adapters.md](adapters.md) | Integrating LLMs and databases |
| [cli.md](cli.md) | Command reference |
| [examples.md](examples.md) | Real-world examples |

---

*PEX v0.3 — Under active development*
