# PEX Language

PEX (*Programs intention, not implementation*) es un lenguaje de programación cognitivo diseñado para la era de la inteligencia artificial.

## Filosofía

Durante décadas, los lenguajes de programación fueron creados para controlar máquinas mediante instrucciones precisas y deterministas. PEX nace para un nuevo contexto: **colaborar con inteligencias artificiales**.

En lugar de describir cada paso de un algoritmo, en PEX el programador describe:
- Intenciones (tasks, agents)
- Contexto (memory, variables)
- Recursos (tools, models)
- Resultados esperados (goals)

El sistema de ejecución (runtime) se encarga de planificar y transformar esas intenciones en acciones concretas usando modelos de IA y herramientas.

## Sintaxis v0.1

PEX utiliza una sintaxis limpia, mínima y basada en indentación. Los archivos usan la extensión `.pi`.

### Ejemplo Básico

```pex
task hello
   goal say hello to the world and introduce PEX
```

### Ejemplo Completo

```pex
# Variables
region = "latam"

# Modelos y Herramientas
model analyst
   provider openai
   name gpt-4

tool sales_db
   provider postgres
   source $SALES_DB_URL

# Tareas
task analyze_sales
   input sales_db
   context region
   model analyst
   goal identify trends in monthly sales
   output trends

task predict_sales
   input trends
   model analyst
   goal predict next month revenue
   output forecast

# Pipelines
pipeline monthly_analysis
   step analyze_sales
   step predict_sales
```

## Uso del Intérprete

Este repositorio contiene la implementación v0.1 del intérprete en Python. Actualmente funciona en modo *dry-run* (simulación de ejecución).

### Ejecutar un programa

```bash
python main.py run examples/demo.pi
```

### Verificar sintaxis

```bash
python main.py check examples/hello.pi
```

## Estructura del Proyecto

- `pex/lexer.py` - Tokenizador que maneja la indentación.
- `pex/parser.py` - Analizador sintáctico descendente recursivo.
- `pex/ast_nodes.py` - Definición de los nodos del AST.
- `pex/runtime.py` - Motor de ejecución simulada.
- `pex/cli.py` - Interfaz de línea de comandos.

---
*PEX programs intelligence.*
