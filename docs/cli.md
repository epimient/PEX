# PEX Command Line Interface

## Usage

```bash
python main.py <command> <file.pi> [flags]
```

---

## Commands

### run

Execute a PEX program.

```bash
python main.py run program.pi
```

**Flags:**
- `--dry-run` — Simulate execution without calling real adapters (LLM, DB)
- `--verbose` — Show detailed execution information

**Example:**
```bash
# Full execution
python main.py run sales.pi

# Dry run (simulation only)
python main.py run sales.pi --dry-run

# Verbose output
python main.py run sales.pi --verbose
```

---

### check

Verify syntax and semantics without executing.

```bash
python main.py check program.pi
```

**Output:**
```
  ✓ Sintaxis y semántica correctas

  📋 Tasks: 3 │ 🤖 Agents: 1 │ 🔗 Pipelines: 1

  ─────────────────────────────────────────────────
  PEX — Programs intention, not implementation.
```

---

### ast

Display the Abstract Syntax Tree.

```bash
python main.py ast program.pi
```

**Flags:**
- `--json` — Output as JSON
- `--full` — Show complete strings (not truncated)

**Example:**
```bash
# Hierarchical view
python main.py ast program.pi

# JSON output
python main.py ast program.pi --json

# Full strings
python main.py ast program.pi --json --full
```

**Output (hierarchical):**
```
PEX AST
Archivo: program.pi

Program
└── TaskBlock(name=hello) [L1]
    └── goal: StringLiteral("say hello")
```

---

### plan

Display the execution plan.

```bash
python main.py plan program.pi
```

**Flags:**
- `--json` — Output as JSON
- `--verbose` — Show detailed step information
- `--summary` — Show only summary

**Example:**
```bash
# Full plan
python main.py plan pipeline.pi

# JSON output
python main.py plan pipeline.pi --json

# Summary only
python main.py plan pipeline.pi --summary
```

**Output:**
```
PEX Execution Plan
Archivo: pipeline.pi
Proyecto: sales_analysis

Plan Summary
  - tasks: 3
  - pipelines: 1
  - tools: 2
  - models: 1

Pipeline: monthly_report
  ────────────────────────────────────────
  Step 1 — analyze_sales
    kind: task
    input: ['sales_db']
    actions:
      - resolve inputs
      - execute sql
      - solve goal via LLM
      - store output in 'trends'
```

---

### version

Show PEX version.

```bash
python main.py version
```

**Output:**
```
  PEX v0.3.0
```

---

### help (no command)

Show usage information.

```bash
python main.py
```

**Output:**
```
  PEX — Intérprete v0.3.0

  Uso:
    python main.py ast     <archivo.pi>   [--json] [--full]
    python main.py plan    <archivo.pi>   [--json] [--verbose]
    python main.py run     <archivo.pi>   [--dry-run] [--verbose]
    python main.py check   <archivo.pi>
    python main.py version

  Flags adicionales:
    --json      Salida en formato JSON
    --full      Mostrar cadenas completas
    --verbose   Detalles extra
    --dry-run   Simular ejecución
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (syntax, semantic, runtime) |

---

## Environment Variables

PEX reads from `.env` file automatically:

```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4
DATABASE_URL=postgres://localhost/db
```

---

## Examples

### Basic Check

```bash
python main.py check hello.pi
```

### Run with Dry-Run

```bash
python main.py run pipeline.pi --dry-run
```

### AST as JSON

```bash
python main.py ast program.pi --json > ast.json
```

### Verbose Plan

```bash
python main.py plan complex.pi --verbose
```

---

*PEX CLI v0.3*
