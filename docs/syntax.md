# PEX Syntax Guide

## Overview

PEX uses a clean, minimal syntax based on indentation (like Python). Files use the `.pi` extension.

## Basic Rules

### 1. Indentation Defines Blocks

```pex
task analyze
   input data
   goal analyze the data
   output result
```

### 2. Keywords + Names Start Blocks

```pex
<keyword> <name>
   <property> <value>
```

### 3. No Braces or Semicolons

No `{}`, `;`, or mandatory `:`.

### 4. Variables Use `=`

```pex
region = "latam"
limit = 100
debug = true
```

### 5. Comments Start with `#`

```pex
# This is a comment
task hello
   # Another comment
   goal say hello
```

---

## Block Types

### project

Defines the main project unit.

```pex
project sales_ai
   import tools
   import models
   import tasks
```

### task

Basic unit of intention.

```pex
task analyze_sales
   input sales_db
   context region
   use web_search
   model analyst
   goal identify trends in monthly sales
   output trends
```

**Properties:**
- `input <source>` — Data source (can be repeated)
- `context <ctx>` — Context variable (can be repeated)
- `use <tool>` — Tool reference (can be repeated)
- `model <model>` — AI model reference
- `goal <text>` — Objective description
- `output <ident>` — Output name
- `sql """..."""` — SQL query (multiline)
- `query <text>` — File query instruction

### agent

Intelligent entity with purpose.

```pex
agent market_researcher
   model analyst
   use web_search
   use docs
   goal investigate current market trends in AI
   output market_report
```

**Properties:**
- `goal <text>` — Objective
- `model <model>` — AI model reference
- `use <tool>` — Tool reference (can be repeated)

### pipeline

Composes tasks or agents.

```pex
pipeline monthly_analysis
   step analyze_sales
   step predict_sales
   step generate_report
```

**Properties:**
- `step <task_or_agent>` — Reference to task/agent (can be repeated)

### tool

Declares external capability.

```pex
tool sales_db
   provider postgres
   source $SALES_DB_URL

tool web_search
   provider web

tool local_file
   provider csv
   source "data/sales.csv"
```

**Properties:**
- `provider <provider>` — Provider type (sqlite, postgres, openai, csv, json, etc.)
- `source <source>` — Connection string or path

### model

Declares AI model access.

```pex
model analyst
   provider openai
   name $OPENAI_MODEL

model local_model
   provider ollama
   name llama3
```

**Properties:**
- `provider <provider>` — Provider (openai, ollama, etc.)
- `name <model_name>` — Model identifier

### memory

Defines contextual memory resource.

```pex
memory session_context
   scope session

memory user_profile
   scope persistent
```

**Properties:**
- `scope <scope>` — Memory scope (session, project, persistent)

### record

Lightweight data structure.

```pex
record Forecast
   revenue
   confidence
   explanation
```

**Properties:**
- Field names listed directly

### entity

Domain model with table mapping.

```pex
entity Sale
   table sales
   field sale_id
   field product_name
   field revenue
   field sale_date
```

**Properties:**
- `table <table_name>` — Database table
- `field <field_name>` — Field name (can be repeated)

---

## Literals

### Strings

```pex
region = "latam"
goal "analyze the data"
```

### Numbers

```pex
limit = 100
temperature = 0.2
```

### Booleans

```pex
debug = true
enabled = false
```

### Environment Variables

```pex
source $DATABASE_URL
name $OPENAI_MODEL
```

---

## Multiline Blocks

Use `"""` for SQL, queries, or complex text:

```pex
task get_sales
   input sales_db
   sql """
       SELECT product, region, SUM(revenue) as total
       FROM sales
       WHERE date >= current_date - interval '12 months'
       GROUP BY product, region
       ORDER BY total DESC
   """
   output sales_data
```

---

## Complete Example

```pex
# Sales Analysis Pipeline
project sales_analysis

# Configuration
region = "latam"
debug = true

# Models
model analyst
   provider openai
   name gpt-4

# Tools
tool sales_db
   provider sqlite
   source $SALES_DB_URL

tool web_search
   provider web

# Memory
memory session_context
   scope session

# Data Structures
record Forecast
   revenue
   confidence
   explanation

# Tasks
task analyze_sales
   input sales_db
   context region
   model analyst
   goal identify trends in monthly sales data
   output trends

task predict_sales
   input trends
   model analyst
   goal predict next month revenue with confidence score
   output forecast

task generate_report
   input trends
   input forecast
   use web_search
   goal generate executive summary report with charts
   output report

# Agent
agent market_researcher
   model analyst
   use web_search
   goal investigate current market conditions in the region

# Main Pipeline
pipeline monthly_analysis
   step analyze_sales
   step predict_sales
   step generate_report
```

---

## Syntax Summary Table

| Block | Purpose | Key Properties |
|-------|---------|----------------|
| `project` | Main unit | `import` |
| `task` | Intention | `input`, `goal`, `output`, `sql`, `model` |
| `agent` | Intelligent entity | `goal`, `model`, `use` |
| `pipeline` | Orchestration | `step` |
| `tool` | External resource | `provider`, `source` |
| `model` | AI model | `provider`, `name` |
| `memory` | Context storage | `scope` |
| `record` | Data structure | fields |
| `entity` | Domain model | `table`, `field` |

---

*PEX Syntax v0.3*
