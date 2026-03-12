# PEX Examples

## Hello World

The simplest PEX program:

```pex
# hello.pi
task hello
   goal say hello to the world and introduce PEX
```

**Run:**
```bash
python main.py run hello.pi
```

---

## Database Query

Query a SQLite database and analyze results:

```pex
# sales_query.pi
project sales_demo

tool sales_db
   provider sqlite
   source $SALES_DB_URL

model analyst
   provider openai
   name gpt-4

task get_top_products
   input sales_db
   sql """
       SELECT product, SUM(revenue) as total
       FROM sales
       WHERE year = 2025
       GROUP BY product
       ORDER BY total DESC
       LIMIT 10
   """
   output top_products

task analyze_performance
   input top_products
   model analyst
   goal identify the top 3 products and explain why they might be performing well
   output analysis

pipeline sales_analysis
   step get_top_products
   step analyze_performance
```

**Environment (.env):**
```bash
SALES_DB_URL=sqlite://./sales.db
OPENAI_API_KEY=sk-xxxxx
```

**Run:**
```bash
python main.py run sales_query.pi
```

---

## AI Pipeline

Multi-step AI analysis pipeline:

```pex
# research.pi
project market_research

model researcher
   provider openai
   name gpt-4

tool web_search
   provider web

# Step 1: Gather information
task gather_data
   use web_search
   goal search for recent AI trends in healthcare
   output raw_data

# Step 2: Analyze trends
task analyze_trends
   input raw_data
   model researcher
   goal identify the top 5 emerging trends and their potential impact
   output trends

# Step 3: Generate report
task generate_report
   input trends
   model researcher
   goal create a concise executive summary with actionable recommendations
   output final_report

pipeline research_workflow
   step gather_data
   step analyze_trends
   step generate_report
```

**Run:**
```bash
python main.py run research.pi
```

---

## Multi-File Project

Organize large projects with imports:

**main.pi:**
```pex
project sales_ai
   import tools
   import models
   import tasks
   import pipelines
```

**tools.pi:**
```pex
tool sales_db
   provider postgres
   source $SALES_DB_URL

tool crm_db
   provider postgres
   source $CRM_DB_URL

tool analytics
   provider bigquery
   source $GCP_PROJECT
```

**models.pi:**
```pex
model analyst
   provider openai
   name gpt-4

model predictor
   provider openai
   name gpt-4-turbo
```

**tasks.pi:**
```pex
task analyze_sales
   input sales_db
   model analyst
   goal analyze monthly sales trends
   output sales_analysis

task predict_revenue
   input sales_analysis
   model predictor
   goal forecast next quarter revenue
   output forecast
```

**pipelines.pi:**
```pex
pipeline monthly_report
   step analyze_sales
   step predict_revenue
```

**Run:**
```bash
python main.py run main.pi
```

---

## Local LLM (Ollama)

Use local models instead of OpenAI:

```pex
# local_ai.pi
model local_assistant
   provider ollama
   name llama3

task summarize
   input document
   model local_assistant
   goal summarize the key points in 3 bullets
   output summary
```

**Environment (.env):**
```bash
OLLAMA_HOST=http://localhost:11434
```

**Requirements:**
```bash
pip install requests
ollama serve  # In another terminal
```

**Run:**
```bash
python main.py run local_ai.pi
```

---

## File Processing

Read and analyze CSV/JSON files:

```pex
# file_analysis.pi
project file_processor

tool data_file
   provider csv
   source "data/sales.csv"

model analyst
   provider openai
   name gpt-4

task load_data
   input data_file
   goal load and parse the CSV file
   output raw_data

task find_insights
   input raw_data
   model analyst
   goal identify sales patterns and anomalies
   output insights

pipeline file_workflow
   step load_data
   step find_insights
```

**Sample CSV (data/sales.csv):**
```csv
date,product,region,revenue
2025-01-01,Widget A,latam,15000
2025-01-02,Widget B,na,22000
2025-01-03,Widget A,eu,18000
```

**Run:**
```bash
python main.py run file_analysis.pi
```

---

## Agent System

Multi-agent collaboration:

```pex
# agents.pi
project agent_team

model strategist
   provider openai
   name gpt-4

model writer
   provider openai
   name gpt-4

tool research_db
   provider web

# Agent 1: Research
agent researcher
   model strategist
   use research_db
   goal gather comprehensive information about market trends
   output research_findings

# Agent 2: Analysis
agent analyst
   model strategist
   goal analyze research findings and identify opportunities
   output analysis

# Agent 3: Writing
agent writer
   model writer
   goal write a detailed report based on the analysis
   output final_report

pipeline content_creation
   step researcher
   step analyst
   step writer
```

**Run:**
```bash
python main.py run agents.pi
```

---

## Data Structures

Using records and entities:

```pex
# structured.pi
project structured_data

# Define data structure
record Forecast
   revenue
   confidence
   explanation

entity Customer
   table customers
   field customer_id
   field name
   field email
   field total_purchases

tool db
   provider sqlite
   source ":memory:"

model analyst
   provider openai
   name gpt-4

task get_customers
   input db
   sql SELECT * FROM customers
   output customer_list

task segment_customers
   input customer_list
   model analyst
   goal segment customers by purchase behavior
   output segments

pipeline customer_analysis
   step get_customers
   step segment_customers
```

**Run:**
```bash
python main.py run structured.pi
```

---

## Error Handling Example

See how PEX reports errors:

```pex
# errors.pi
project broken

# Error 1: Duplicate task name
task analyze
   goal first task

task analyze  # ← Duplicate!
   goal second task

# Error 2: Undefined reference
pipeline main
   step analyze
   step nonexistent  # ← Doesn't exist!
```

**Check:**
```bash
python main.py check errors.pi
```

**Output:**
```
  ✗ [ERROR] E001: Task duplicada: 'analyze'
     📍 errors.pi:8
     💡 Sugerencia: Renombra una de las tasks o elimina la definición redundante.

  ✗ [ERROR] E008: Pipeline 'main' tiene step 'nonexistent' que no es task ni agent
     📍 errors.pi:14
     💡 Sugerencia: Define 'nonexistent' como task o agent antes del pipeline.
```

---

## Best Practices

### 1. Use Descriptive Names

```pex
# Good
task analyze_monthly_sales_trends

# Avoid
task do_stuff
```

### 2. One Goal Per Task

```pex
# Good
task extract_data
   goal extract raw data from database

task transform_data
   goal clean and normalize the data

# Avoid
task everything
   goal extract, transform, analyze, and report
```

### 3. Use Imports for Organization

```pex
# main.pi
project sales_system
   import tools
   import models
   import tasks
   import pipelines
```

### 4. Document with Comments

```pex
# Customer segmentation pipeline
# Runs monthly to identify high-value segments
pipeline monthly_segmentation
   step load_customers
   step segment_by_value
   step generate_targets
```

---

## Bot Vendedor de Carros (Batch)

Un ejemplo completo de flujo de ventas automatizado:

```pex
# bot_vendedor_carros.pi
project bot_vendedor_carros

model vendedor_asistente
   provider ollama
   name "llama3:8b"

tool inventario_autos
   provider file
   source inventario_carros.json

task saludar_cliente
   model vendedor_asistente
   goal Eres un vendedor de carros profesional. Saluda al cliente de manera cálida.
   output saludo_inicial

task consultar_inventario
   input inventario_autos
   model vendedor_asistente
   goal Filtra los autos que coincidan con las preferencias del cliente.
   output autos_sugeridos

task generar_recomendacion
   model vendedor_asistente
   goal Recomienda el mejor auto explicando por qué es ideal.
   output recomendacion_final

pipeline flujo_venta_completo
   step saludar_cliente
   step consultar_inventario
   step generar_recomendacion
```

**Run:**
```bash
pex run examples/bot_vendedor_carros.pi
```

---

## Bot Conversacional (Interactivo)

Chat en tiempo real con el vendedor de carros:

```bash
cd examples
python3 pex_chat.py
```

Esto inicia una conversación interactiva:

```
╔══════════════════════════════════════════════════════════════╗
║     🤖 PEX BOT VENDEDOR DE CARROS - CONVERSACIONAL         ║
║                    Premium Auto                              ║
╚══════════════════════════════════════════════════════════════╝

🤖 Bot: ¡Bienvenido a Premium Auto! Soy Alex, tu asesor de ventas. 
¿En qué puedo ayudarte hoy?

👤 Tú: Busco un auto familiar
🤖 Bot: ¡Excelente elección! Para una familia, te recomiendo el Hyundai Santa Fe...
```

---

## Ollama con Inventario

Combina Ollama local con herramientas de archivo:

```pex
# ollama_test.pi
project ollama_test

model assistant
   provider ollama
   name "llama3:8b"

tool inventario
   provider file
   source inventario_carros.json

task greet
   model assistant
   goal Eres un asistente amigable. Saluda al usuario.
   output greeting

pipeline hello
   step greet
```

**Run:**
```bash
pex run examples/ollama_test.pi
```

**Nota:** Si el modelo tiene `:` en el nombre, usa comillas:
```pex
name "llama3:8b"
```

---

*PEX Examples v0.4*
