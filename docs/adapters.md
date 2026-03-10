# PEX Adapters

Adapters are the plugin system that connects PEX to external services (LLMs, databases, files).

---

## LLM Adapters

### OpenAI

**Configuration:**
```pex
model analyst
   provider openai
   name gpt-4
```

**Environment:**
```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4
```

**Requirements:**
```bash
pip install openai
```

**Usage:**
```pex
task analyze
   model analyst
   goal analyze the sales data and identify trends
   output insights
```

---

### Ollama (Local)

**Configuration:**
```pex
model local_ai
   provider ollama
   name llama3
```

**Environment:**
```bash
OLLAMA_HOST=http://localhost:11434
```

**Requirements:**
```bash
pip install requests
ollama pull llama3
ollama serve
```

**Usage:**
```pex
task summarize
   model local_ai
   goal summarize the document
   output summary
```

---

## Database Adapters

### SQLite

**Configuration:**
```pex
tool local_db
   provider sqlite
   source "data.db"
```

**Or in-memory:**
```pex
tool temp_db
   provider sqlite
   source ":memory:"
```

**Usage:**
```pex
task query_db
   input local_db
   sql """
       SELECT * FROM sales
       WHERE date > '2025-01-01'
   """
   output results
```

---

### PostgreSQL

**Configuration:**
```pex
tool production_db
   provider postgres
   source $DATABASE_URL
```

**Environment:**
```bash
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
```

**Requirements:**
```bash
pip install psycopg2-binary
```

**Usage:**
```pex
task get_customers
   input production_db
   sql SELECT * FROM customers
   output customer_list
```

---

## File Adapters

### CSV

**Configuration:**
```pex
tool sales_csv
   provider csv
   source "data/sales.csv"
```

**Usage:**
```pex
task load_csv
   input sales_csv
   goal load and parse the CSV file
   output data
```

---

### JSON

**Configuration:**
```pex
tool config_json
   provider json
   source "config.json"
```

**Usage:**
```pex
task load_config
   input config_json
   goal load configuration settings
   output config
```

---

### Text/Markdown

**Configuration:**
```pex
tool document
   provider txt
   source "docs/readme.md"
```

**Usage:**
```pex
task read_doc
   input document
   goal read and summarize the document
   output summary
```

---

## Creating Custom Adapters

### LLM Adapter

```python
# pex/adapters/llm.py
from pex.adapters import LLMAdapter

class CustomLLMAdapter(LLMAdapter):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        # Initialize your client
        self.is_configured = True
    
    def execute_intent(self, goal: str, inputs: dict, context: dict) -> str:
        # Your LLM logic here
        response = self.client.generate(goal, inputs, context)
        return response
```

**Register in factory:**
```python
# pex/adapters/__init__.py
def get_llm_adapter(provider: str, model_name: str, **kwargs):
    if provider == "custom":
        from pex.adapters.llm import CustomLLMAdapter
        return CustomLLMAdapter(model_name, **kwargs)
```

---

### Database Adapter

```python
# pex/adapters/db.py
from pex.adapters import DBAdapter
from typing import List, Dict, Any

class MySQLAdapter(DBAdapter):
    def __init__(self, source_url: str):
        super().__init__(source_url)
        import mysql.connector
        self.module = mysql.connector
        self.is_configured = True
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        conn = self.module.connect(self.source_url)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        return cursor.fetchall()
```

---

### File Adapter

```python
# pex/adapters/file.py
from pex.adapters.file import FileAdapter

class XMLAdapter(FileAdapter):
    def __init__(self, source_path: str, format_type: str = "xml"):
        super().__init__(source_path, format_type)
    
    def execute_query(self, query: str):
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.source_path)
        root = tree.getroot()
        # Parse based on query
        return self._parse_xml(root, query)
```

---

## Adapter Status

| Provider | Type | Status | Requirements |
|----------|------|--------|--------------|
| `openai` | LLM | ✅ Built-in | `openai` package |
| `ollama` | LLM | ✅ Built-in | `requests` package |
| `sqlite` | DB | ✅ Built-in | None (stdlib) |
| `postgres` | DB | ✅ Built-in | `psycopg2-binary` |
| `csv` | File | ✅ Built-in | None (stdlib) |
| `json` | File | ✅ Built-in | None (stdlib) |
| `txt` | File | ✅ Built-in | None (stdlib) |
| `mysql` | DB | 🔌 Custom | Implement adapter |
| `bigquery` | DB | 🔌 Custom | Implement adapter |

---

## Best Practices

### 1. Use Environment Variables

```pex
# Good
tool db
   provider postgres
   source $DATABASE_URL

# Avoid
tool db
   provider postgres
   source "postgres://user:pass@localhost/db"
```

### 2. Graceful Degradation

Adapters should work in simulation mode if not configured:

```python
def execute_intent(self, goal, inputs, context):
    if not self.is_configured:
        return f"[Simulated] Goal: {goal}"
    # Real execution
```

### 3. Error Handling

Return structured errors, don't crash:

```python
def execute_query(self, sql):
    try:
        # Execute query
        return results
    except Exception as e:
        return [{"error": f"Query failed: {str(e)}"}]
```

---

*PEX Adapters v0.3*
