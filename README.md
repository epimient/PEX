# PEX Language

PEX (*Programs intention, not implementation*) es un lenguaje de programación cognitivo diseñado para la era de la inteligencia artificial.

## Filosofía

Durante décadas, los lenguajes de programación fueron creados para controlar máquinas mediante instrucciones precisas y deterministas. PEX nace para un nuevo contexto: **colaborar con inteligencias artificiales**.

En lugar de describir cada paso de un algoritmo, en PEX el programador describe:
- **Intenciones** (`task`, `agent`, `pipeline`)
- **Contexto** (`memory`, `variables`, `context`)
- **Recursos** (`tool`, `model`)
- **Estructura de Datos** (`record`, `entity`)

## Sintaxis v0.4 (Tipos, Caché, MCP, Linter)

PEX utiliza una sintaxis limpia, mínima y basada en indentación. Los archivos usan la extensión `.pi`.

### Novedades en v0.4:
- **Sistema de Tipos**: Annotations opcionales para records y entities (`field : type`)
- **Caché Integrada**: Memory blocks con TTL para cacheo automático de resultados
- **Integración MCP**: Soporte para Model Context Protocol (tools, resources, prompts, LLMs)
- **Linter Estático**: Análisis de código con `pex lint` (variables no usadas, naming conventions, etc.)
- **Imports Relativos**: Soporte para `../modules/foo` y paths con strings

### Ejemplo: Tipos en Records
```pex
record Forecast
    revenue : float
    confidence : int
    explanation : string
```

### Ejemplo: Caché con TTL
```pex
memory session_cache
    scope session
    ttl 60  # segundos
```

### Ejemplo: MCP Integration
```pex
tool web_search
    provider mcp
    source http://localhost:8080

model local_ai
    provider mcp
    name llama3
```

### Ejemplo: Arquitectura Multi-Archivo
`database.pi`
```pex
tool sales_db
    provider "postgres"
    source $SALES_DB_URL
```

`main.pi`
```pex
project Analytics
    import database # Carga definiciones de database.pi

# Variables Globales
region = "latam"

# Definición de Modelos
model analyst
    provider "openai"
    name "gpt-4"

# Tarea con lógica de IA
task predictor
    input products_data
    model analyst
    goal "Predict seasonal sales trends based on input"
    output forecast_report

# Pipeline: Orquestación de pasos
pipeline annual_forecast
    step fetchData
    step predictor
```

## Arquitectura del Intérprete

La versión 0.4 consolida la arquitectura en capas para garantizar robustez:

1.  **Lexer & Parser**: Procesan el código fuente. El lexer maneja indentación (estilo Python), bloques de texto libre, y annotations de tipos (`:`).
2.  **Registry & Symbol Table**: Centraliza todas las definiciones. Implementa **detección de colisiones** y almacena información de tipos.
3.  **Execution Planner**: La "mente" del compilador. Resuelve imports recursivos (incluyendo relativos `../`), valida referencias, y genera un `ExecutionPlan` validado.
4.  **Cache**: Sistema de caché en memoria con TTL para resultados de ejecución.
5.  **Runtime**: Motor de ejecución. Traduce el plan en acciones. Soporta modos "check", "run", "dry-run", y caché automático.
6.  **Linter**: Análisis estático opcional para detectar problemas comunes y sugerir mejoras.

## Uso del Intérprete (CLI)

### Instalación
Asegúrate de tener Python 3.10+ instalado. No requiere dependencias externas para la ejecución básica.

### Comandos Principales

#### 1. Mostrar el AST (Jerárquico o JSON)
```bash
python3 main.py ast path/to/file.pi
# O con banderas
python3 main.py ast path/to/file.pi --json --full
```

#### 2. Visualizar el plan de ejecución
```bash
python3 main.py plan path/to/file.pi
# O modo detallado para depuración
python3 main.py plan path/to/file.pi --verbose
```

#### 3. Verificar integridad semántica
```bash
python3 main.py check path/to/file.pi
```

#### 4. Ejecutar programa
```bash
python3 main.py run path/to/file.pi
# Modo simulación (sin llamar adapters reales)
python3 main.py run path/to/file.pi --dry-run
```

#### 5. Analizar código estáticamente (NUEVO en v0.4)
```bash
python3 main.py lint path/to/file.pi
# Con warnings e info
python3 main.py lint path/to/file.pi --verbose
```

#### 6. Mostrar versión
```bash
python3 main.py version
```

## Estructura del Código
- `pex/lexer.py`: Motor léxico con soporte `"""` y type annotations (`:`).
- `pex/ast_nodes.py`: Nodos del AST con tipos `ValueNode`/`TextNode`, `RecordField`, `EntityField`.
- `pex/ast_utils.py`: Visualización y serialización del AST.
- `pex/parser.py`: Parser estricto sincronizado con el AST.
- `pex/registry.py`: Gestión de símbolos, errores semánticos y tipos.
- `pex/planner.py`: Resolución de dependencias, imports (absolutos y relativos).
- `pex/cache.py`: Sistema de caché con TTL (NUEVO en v0.4).
- `pex/linter.py`: Análisis estático de código (NUEVO en v0.4).
- `pex/runtime.py`: Orquestador de la ejecución con caché automático.
- `pex/adapters/`: Adapters para LLMs, BDs, Files y **MCP** (NUEVO en v0.4).

## Métricas del Proyecto (v0.4)

- **172 tests** automatizados
- **~4400 líneas** de código Python
- **10 adapters** disponibles (OpenAI, Ollama, SQLite, Postgres, MCP, etc.)
- **6 comandos CLI** (ast, plan, check, run, lint, version)
- **15+ reglas** de linter

---
*PEX v0.4 — Programs intention, not implementation.*
