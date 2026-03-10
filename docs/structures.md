# PEX Structures

PEX programs are built from these core structures.

---

## project

**Purpose:** Main project unit that groups related components.

**Syntax:**
```pex
project <name>
   import <module>
   import <module>
```

**Example:**
```pex
project sales_analysis
   import tools
   import models
   import tasks
   import pipelines
```

**Notes:**
- One project per main file
- Imports are resolved relative to the project file
- Import order doesn't matter (all loaded before execution)

---

## task

**Purpose:** Basic unit of intention — describes what to accomplish.

**Syntax:**
```pex
task <name>
   input <source>
   context <variable>
   use <tool>
   model <model>
   goal <description>
   sql """..."""
   query <instruction>
   output <result_name>
```

**Example:**
```pex
task analyze_sales
   input sales_db
   context region
   use web_search
   model analyst
   goal identify trends in monthly sales data
   sql """
       SELECT month, SUM(revenue) as total
       FROM sales
       GROUP BY month
       ORDER BY month
   """
   output trends
```

**Properties:**

| Property | Type | Repeatable | Description |
|----------|------|------------|-------------|
| `input` | Reference | Yes | Data source (tool, variable, or output) |
| `context` | Reference | Yes | Context variable |
| `use` | Reference | Yes | Tool reference |
| `model` | Reference | No | AI model reference |
| `goal` | Text | No | Objective description |
| `sql` | Text (multiline) | No | SQL query to execute |
| `query` | Text | No | File query instruction |
| `output` | Identifier | No | Output name |

---

## agent

**Purpose:** Intelligent entity with autonomous behavior.

**Syntax:**
```pex
agent <name>
   model <model>
   use <tool>
   goal <description>
   output <result_name>
```

**Example:**
```pex
agent market_researcher
   model analyst
   use web_search
   use docs
   goal investigate current market trends and competitive landscape
   output market_report
```

**Properties:**

| Property | Type | Repeatable | Description |
|----------|------|------------|-------------|
| `model` | Reference | No | AI model reference |
| `use` | Reference | Yes | Tool reference |
| `goal` | Text | No | Objective |
| `output` | Identifier | No | Output name |

**Agent vs Task:**
- **Task:** Single intention, explicit steps
- **Agent:** Autonomous entity, may have internal reasoning loop

---

## pipeline

**Purpose:** Orchestrates tasks and agents in sequence.

**Syntax:**
```pex
pipeline <name>
   step <task_or_agent>
   step <task_or_agent>
```

**Example:**
```pex
pipeline monthly_report
   step analyze_sales
   step predict_revenue
   step generate_presentation
```

**Properties:**

| Property | Type | Repeatable | Description |
|----------|------|------------|-------------|
| `step` | Reference | Yes | Reference to task or agent |

**Notes:**
- Steps execute in order
- Output of one step can be input to next
- Pipeline validates all steps exist before execution

---

## tool

**Purpose:** Declares external resource or capability.

**Syntax:**
```pex
tool <name>
   provider <provider>
   source <connection>
```

**Example:**
```pex
tool sales_db
   provider postgres
   source $SALES_DB_URL

tool web_search
   provider web

tool local_data
   provider csv
   source "data/sales.csv"
```

**Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `provider` | String | Yes | Provider type |
| `source` | String/Env | No | Connection string or path |

**Providers:**

| Provider | Type | Description |
|----------|------|-------------|
| `sqlite` | Database | SQLite database |
| `postgres` | Database | PostgreSQL database |
| `openai` | LLM | OpenAI API |
| `ollama` | LLM | Local Ollama models |
| `csv` | File | CSV file |
| `json` | File | JSON file |
| `txt` | File | Text/Markdown file |
| `web` | Tool | Web search capability |

---

## model

**Purpose:** Declares AI model access.

**Syntax:**
```pex
model <name>
   provider <provider>
   name <model_name>
```

**Example:**
```pex
model analyst
   provider openai
   name gpt-4

model local_model
   provider ollama
   name llama3
```

**Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `provider` | String | Yes | Provider type |
| `name` | String/Env | Yes | Model identifier |

---

## memory

**Purpose:** Defines contextual memory resource.

**Syntax:**
```pex
memory <name>
   scope <scope>
```

**Example:**
```pex
memory session_context
   scope session

memory user_profile
   scope persistent
```

**Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `scope` | String | No | Memory scope |

**Scopes:**
- `session` — Current execution session
- `project` — Project-wide
- `persistent` — Across sessions (future feature)

---

## record

**Purpose:** Lightweight data structure (like a struct).

**Syntax:**
```pex
record <name>
   field_name
   field_name
```

**Example:**
```pex
record Forecast
   revenue
   confidence
   explanation
   generated_at
```

**Notes:**
- Fields listed directly (no types in v0.3)
- Used for output validation (future)
- Similar to Python dataclasses

---

## entity

**Purpose:** Domain model with database mapping.

**Syntax:**
```pex
entity <name>
   table <table_name>
   field <field_name>
   field <field_name>
```

**Example:**
```pex
entity Customer
   table customers
   field customer_id
   field name
   field email
   field total_purchases
```

**Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `table` | String | No | Database table name |
| `field` | String | Yes | Field name (repeatable) |

---

## Variables

**Purpose:** Simple value assignments.

**Syntax:**
```pex
name = value
```

**Example:**
```pex
region = "latam"
period = "last_12_months"
limit = 100
debug = true
temperature = 0.2
```

**Types:**
- String: `"value"` or `'value'`
- Number: `100`, `3.14`
- Boolean: `true`, `false`
- Environment: `$VAR_NAME`

**Usage:**
```pex
task analyze
   context region
   context period
   goal analyze data for region
```

---

## Structure Relationships

```
project
├── imports tools
│   └── tool sales_db
├── imports models
│   └── model analyst
├── imports tasks
│   └── task analyze_sales
│       ├── input → sales_db (tool)
│       └── model → analyst (model)
└── imports pipelines
    └── pipeline monthly_report
        └── step → analyze_sales (task)
```

---

## Naming Conventions

| Structure | Convention | Example |
|-----------|------------|---------|
| project | snake_case | `sales_analysis` |
| task | snake_case | `analyze_sales` |
| agent | snake_case | `market_researcher` |
| pipeline | snake_case | `monthly_report` |
| tool | snake_case | `sales_db` |
| model | snake_case | `analyst` |
| record | PascalCase | `Forecast` |
| entity | PascalCase | `Customer` |
| variable | snake_case | `region` |

---

*PEX Structures v0.3*
