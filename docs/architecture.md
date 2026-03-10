# PEX Architecture

## Overview

PEX is an **interpreted cognitive programming language** with an **intelligent execution planner**.

```
PEX code (.pi)
     ↓
Lexer → Tokens
     ↓
Parser → AST
     ↓
Registry → Symbol Table
     ↓
Planner → Execution Plan
     ↓
Runtime → Execution (with Cache & MCP)
     ↓
Adapters → LLMs, Databases, Files, MCP Servers
     ↓
Linter → Static Analysis (optional)
```

**Version:** v0.4.0

---

## What's New in v0.4

### Type System (Experimental)
```pex
record Forecast
   revenue : float
   confidence : int
   explanation

entity Customer
   table customers
   field id : int
   field email : string
```

### Caching System
```pex
memory session_cache
   scope session
   ttl 60  # seconds
```

### MCP Integration
```pex
tool web_search
   provider mcp
   source http://localhost:8080

model local_ai
   provider mcp
   name llama3
```

### Linter
```bash
python main.py lint program.pi --verbose
```

---

## Components

### 1. Lexer (`pex/lexer.py`)

Converts source code into tokens.

**Features:**
- Indentation handling (Python-style)
- Multiline block support (`"""`)
- Environment variable detection (`$VAR`)
- Comment filtering
- Type annotation support (`:`)

**Token Types:**
- `KEYWORD` — Language keywords (task, agent, pipeline, etc.)
- `IDENT` — Identifiers
- `STRING`, `NUMBER`, `BOOLEAN` — Literals
- `ENV_VAR` — Environment variable references
- `INDENT`, `DEDENT`, `NEWLINE` — Structure tokens
- `COLON` — Type annotations

### 2. Parser (`pex/parser.py`)

Converts tokens into an Abstract Syntax Tree (AST).

**Features:**
- Recursive descent parsing
- Block structure validation
- Property parsing with type validation
- Support for typed fields in records/entities

**AST Node Types:**
- `Program` — Root node
- `TaskBlock`, `AgentBlock`, `PipelineBlock`
- `ToolBlock`, `ModelBlock`, `MemoryBlock`
- `RecordBlock`, `RecordField` — Now with type support
- `EntityBlock`, `EntityField` — Now with type support
- `Assignment` — Variable assignments

### 3. Registry (`pex/registry.py`)

Unified symbol table for all defined components.

**Features:**
- Collision detection (prevents duplicate names)
- Namespace separation by type
- Diagnostic collection
- Type information storage

**Stores:**
- Tasks, Agents, Pipelines
- Tools, Models, Memories
- Records (with field types), Entities (with field types)
- Variables

### 4. Planner (`pex/planner.py`)

Semantic validator and execution planner.

**Phases:**
1. **Import Resolution** — Recursively processes imports (including relative paths)
2. **Symbol Registration** — Registers all definitions
3. **Cross-Reference Validation** — Validates all references

**Validates:**
- Pipeline steps reference valid tasks/agents
- Task inputs exist (tools, variables, or outputs)
- Tools and models are declared
- No import cycles

**Output:** `ExecutionPlan` — Validated program ready for runtime

### 5. Runtime (`pex/runtime.py`)

Execution engine that runs validated plans.

**Modes:**
- **Check** — Syntax and semantics only
- **Run** — Full execution (real or simulated)
- **Dry-Run** — Simulation without real adapter calls

**Features:**
- Adapter initialization (LLM, DB, File, MCP)
- Input/output resolution
- Pipeline orchestration
- Result tracking
- **Caching** — Automatic result caching with TTL

### 5.5 Cache (`pex/cache.py`) — NEW in v0.4

In-memory caching system for execution results.

**Features:**
- TTL-based expiration
- Hit/miss statistics
- Pattern-based invalidation
- Automatic cache key generation from inputs/context

**Usage:**
```python
from pex.cache import Cache, get_global_cache

cache = get_global_cache()
cache.set("key", value, ttl=60)
result = cache.get("key")
stats = cache.stats()  # hits, misses, hit_rate
```

### 6. Adapters (`pex/adapters/`)

Plugin system for external integrations.

**LLM Adapters:**
- `OpenAIAdapter` — OpenAI API
- `OllamaAdapter` — Local Ollama models
- `MCPLLMAdapter` — MCP-compatible models

**Database Adapters:**
- `SQLiteAdapter` — SQLite databases
- `PostgresAdapter` — PostgreSQL databases

**File Adapters:**
- `FileAdapter` — CSV, JSON, TXT files

**MCP Adapters** (NEW in v0.4):
- `MCPToolAdapter` — MCP tools
- `MCPResourceAdapter` — MCP resources
- `MCPPromptAdapter` — MCP prompts

### 7. Linter (`pex/linter.py`) — NEW in v0.4

Static analysis tool for PEX code.

**Rules:**
| Code | Level | Description |
|------|-------|-------------|
| W001 | WARNING | Unused variable |
| W002 | WARNING | Unused import |
| W003 | INFO | Task without output |
| W004 | INFO | Model without provider |
| W005 | WARNING | Empty block (no goal) |
| I001 | HINT | Naming convention violation |

**Usage:**
```bash
python main.py lint program.pi --verbose
```

---

## Execution Flow

### Example Program

```pex
project demo

tool db
   provider sqlite
   source ":memory:"

model ai
   provider openai
   name gpt-4

task query
   input db
   sql SELECT * FROM sales
   output data

task analyze
   input data
   model ai
   goal summarize sales trends
   output summary

pipeline main
   step query
   step analyze
```

### Execution Steps

1. **Lexing**
   ```
   project → KEYWORD
   demo → IDENT
   tool → KEYWORD
   db → IDENT
   ...
   ```

2. **Parsing**
   ```
   Program
   ├── ProjectBlock(demo)
   ├── ToolBlock(db)
   ├── ModelBlock(ai)
   ├── TaskBlock(query)
   ├── TaskBlock(analyze)
   └── PipelineBlock(main)
   ```

3. **Registry**
   ```
   tools: {db: ToolBlock}
   models: {ai: ModelBlock}
   tasks: {query: TaskBlock, analyze: TaskBlock}
   pipelines: {main: PipelineBlock}
   ```

4. **Planning**
   - Resolve imports (none in this case)
   - Validate `pipeline.main` steps reference valid tasks ✓
   - Validate `task.query` input `db` exists ✓
   - Validate `task.analyze` model `ai` exists ✓

5. **Runtime**
   - Initialize SQLite adapter for `db`
   - Initialize OpenAI adapter for `ai`
   - Execute `pipeline.main`:
     - Step 1: `query` → Execute SQL, store in `data`
     - Step 2: `analyze` → Send `data` to OpenAI, store in `summary`

---

## Diagnostic System

PEX uses a unified diagnostic system for errors and warnings.

### Diagnostic Types

- `ERROR` — Compilation failures
- `WARNING` — Potential issues
- `INFO` — Informational messages
- `HINT` — Suggestions

### Error Codes

| Code | Type | Description |
|------|------|-------------|
| L001-L004 | Lexer | Lexical errors |
| S001-S003 | Syntax | Parse errors |
| E001-E009 | Semantic | Semantic errors |
| W001-W004 | Warning | Warnings |
| I001-I002 | Info | Information |

### Example Diagnostic

```
  ✗ [ERROR] E002: Task 'predict' uses input 'monthly_data' 
    but it doesn't exist as tool, variable, or prior output.
  
     📍 tasks.pi:14
     💡 Suggestion: Did you mean 'sales_data'?
```

---

## File Structure

```
PEX/
├── main.py              # Entry point
├── pex/
│   ├── __init__.py
│   ├── lexer.py         # Tokenizer
│   ├── parser.py        # AST generator
│   ├── ast_nodes.py     # AST node definitions
│   ├── ast_utils.py     # AST visualization
│   ├── registry.py      # Symbol table
│   ├── planner.py       # Semantic validator
│   ├── runtime.py       # Execution engine
│   ├── diagnostics.py   # Error system
│   ├── cache.py         # Caching system (v0.4)
│   ├── linter.py        # Static analysis (v0.4)
│   ├── cli.py           # Command interface
│   └── adapters/
│       ├── __init__.py
│       ├── llm.py       # LLM adapters
│       ├── db.py        # Database adapters
│       ├── file.py      # File adapters
│       └── mcp.py       # MCP adapters (v0.4)
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_registry.py
│   ├── test_planner.py
│   ├── test_adapters.py
│   ├── test_cache.py    # Cache tests (v0.4)
│   ├── test_mcp.py      # MCP tests (v0.4)
│   └── test_linter.py   # Linter tests (v0.4)
└── docs/
```

---

## Version History

| Version | Changes |
|---------|---------|
| v0.1 | Initial syntax and parser |
| v0.2 | Runtime with adapters |
| v0.3 | Diagnostic system, import cycle detection, parser refactor |
| **v0.4** | **Type system, caching, MCP integration, linter** |

### v0.4 Details (Current)

**New Features:**
- Type annotations for records and entities (`field : type`)
- In-memory caching with TTL support
- MCP (Model Context Protocol) integration
- Static analysis linter (`pex lint`)
- Relative imports support (`../modules/foo`)

**New Files:**
- `pex/cache.py` — Caching system
- `pex/linter.py` — Static analysis
- `pex/adapters/mcp.py` — MCP adapters
- `tests/test_cache.py`, `tests/test_mcp.py`, `tests/test_linter.py`

**Metrics:**
- 172 automated tests
- ~4400 lines of code
- 10 adapters (6 new in v0.4)
- 6 CLI commands

---

*PEX Architecture v0.4*
