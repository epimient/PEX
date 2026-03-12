# PEX Sales Intelligence Demo

Demostración de análisis predictivo de ventas usando PEX.

## ¿Qué hace esta demo?

1. **Carga datos** de ventas desde una base SQLite
2. **Analiza tendencias** usando IA (OpenAI GPT-4)
3. **Predice revenue** para el próximo mes
4. **Genera reporte** ejecutivo con recomendaciones

## Estructura

```
sales_demo/
├── project.pi       # Proyecto principal
├── tools.pi         # Herramientas (DB, archivos)
├── models.pi        # Modelos de IA
├── tasks.pi         # Tareas definidas
├── pipelines.pi     # Pipelines de orquestación
└── .env.example     # Variables de entorno
```

## Uso

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tu API key de OpenAI
```

### 2. Ejecutar comandos PEX

```bash
# Verificar sintaxis
python main.py check examples/sales_demo/project.pi

# Ver plan de ejecución
python main.py plan examples/sales_demo/project.pi

# Ejecutar (modo simulación)
python main.py run examples/sales_demo/project.pi --dry-run

# Ejecutar (con IA real si tienes API key configurada)
python main.py run examples/sales_demo/project.pi
```

### 3. Ver resultados

El output mostrará:
- Fases de ejecución
- Tools utilizadas
- Modelos invocados
- Outputs generados
- Estadísticas de caché (si aplica)

## Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `check` | Verifica sintaxis y semántica |
| `ast` | Muestra el árbol sintáctico |
| `plan` | Muestra el plan de ejecución |
| `run` | Ejecuta el programa |
| `run --dry-run` | Ejecuta sin llamar APIs reales |
| `lint` | Analiza código estáticamente |

## Qué demuestra

- ✅ **Tools** - Conexión a bases de datos
- ✅ **Models** - Integración con OpenAI
- ✅ **Tasks** - Definición de intenciones
- ✅ **Pipelines** - Orquestación de pasos
- ✅ **SQL** - Consultas multilínea
- ✅ **Outputs** - Encadenamiento de datos
- ✅ **Memory** - Caché de resultados (opcional)

## Requisitos

- Python 3.10+
- `openai` package (para ejecución real)
- `psycopg2-binary` (si usas PostgreSQL)

## Sin API Key

La demo funciona en modo `--dry-run` sin configuración:

```bash
python main.py run examples/sales_demo/project.pi --dry-run
```

Verás la simulación completa sin llamar a APIs externas.

---

*PEX v0.4 — Programs intention, not implementation.*
