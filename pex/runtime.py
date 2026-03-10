"""
PEX Runtime — Motor de ejecución del lenguaje PEX.

En v0.2 opera utilizando un nivel de planificación previo.
Recibe un ExecutionPlan, inicializa los adaptadores declarados,
y ejecuta pipelines o tareas validando las referencias.

Soporte para caché integrado desde v0.4.
"""

from typing import Dict, Any, Optional
import os
import time
from pex.ast_nodes import Program, TaskBlock, AgentBlock, PipelineBlock
from pex.planner import ExecutionPlan
from pex.cache import Cache, get_global_cache

# ─── Colores ANSI para la terminal ───────────────────────────────

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"
    WHITE = "\033[97m"

    HEADER = "\033[1;36m"
    SUCCESS = "\033[1;32m"
    WARN = "\033[1;33m"
    INFO = "\033[1;34m"
    LABEL = "\033[1;35m"

def _c(color: str, text: str) -> str:
    return f"{color}{text}{Colors.RESET}"


# ─── Runtime ─────────────────────────────────────────────────────

class PexRuntime:
    """Motor de ejecución para programas PEX v0.2 con Adapters Reales y Caché."""

    def __init__(self, verbose: bool = True, use_cache: bool = True):
        self.verbose = verbose
        self.use_cache = use_cache

        # Instancias de Adaptadores vivos
        self.llm_adapters: Dict[str, Any] = {}
        self.db_adapters: Dict[str, Any] = {}
        self.file_adapters: Dict[str, Any] = {}

        # Caché para resultados
        self.cache: Optional[Cache] = None
        self.memory_configs: Dict[str, Any] = {}  # Configuración de memory blocks

        # Resultados de ejecución (estado del sistema)
        self.results: Dict[str, Any] = {}
        self.registry = None

    # ── Resolución de valores ────────────────────────────────────

    def _resolve_env(self, name: str) -> str:
        """Resuelve $VARIABLE desde el entorno."""
        val = os.environ.get(name, "")
        if not val:
            return f"$({name} no definida)"
        return val

    def _resolve_value(self, val) -> Any:
        """Resuelve un valor (ya debería ser un nodo AST) a su representación Python."""
        if hasattr(val, "value"):
            return val.value
        elif hasattr(val, "name"):
            name = val.name
            if name.startswith("$"):
                 return self._resolve_env(name[1:])
            if self.registry and name in self.registry.variables:
                return self.registry.variables[name]
            return name
        return str(val) if val else ""

    def _resolve_ref(self, ref: Any) -> Any:
        """Resuelve una referencia (IdentRef, EnvVarRef) o valor literal."""
        from pex.ast_nodes import IdentRef, EnvVarRef, StringLiteral, NumberLiteral, BooleanLiteral

        if isinstance(ref, EnvVarRef):
            return self._resolve_env(ref.name)
        if isinstance(ref, IdentRef):
            # Buscar en variables primero
            if ref.name in self.registry.variables:
                return self.registry.variables[ref.name]
            return ref.name
        if isinstance(ref, (StringLiteral, NumberLiteral, BooleanLiteral)):
            return ref.value
        return str(ref)

    # ── Métodos de Caché ─────────────────────────────────────────

    def _initialize_cache(self):
        """Inicializa la caché basada en los memory blocks configurados."""
        if not self.use_cache:
            return

        self.cache = get_global_cache()

        # Configurar TTLs desde memory blocks
        for name, memory in self.registry.memories.items():
            self.memory_configs[name] = {
                "scope": memory.scope,
                "ttl": memory.ttl,
            }

            if self.verbose and memory.ttl:
                print(f"  💾 Memory '{name}': TTL={memory.ttl}s, scope={memory.scope}")

        if self.verbose and self.cache:
            print(f"  💾 Caché inicializada")

    def _get_cache_key(self, task_name: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Genera clave de caché para una task."""
        return self.cache._make_key(task_name, inputs, context) if self.cache else ""

    def _get_from_cache(self, task_name: str, inputs: Dict, context: Dict) -> Optional[Any]:
        """Intenta obtener resultado de caché."""
        if not self.cache:
            return None

        key = self._get_cache_key(task_name, inputs, context)
        cached = self.cache.get(key)

        if cached is not None and self.verbose:
            print(f"    {_c(Colors.SUCCESS, '✓')} Cache HIT para '{task_name}'")

        return cached

    def _set_in_cache(self, task_name: str, inputs: Dict, context: Dict, result: Any, ttl: Optional[int] = None):
        """Almacena resultado en caché."""
        if not self.cache:
            return

        key = self._get_cache_key(task_name, inputs, context)

        # Usar TTL de memory config si está disponible
        default_ttl = None
        for mem_name, config in self.memory_configs.items():
            if config.get("scope") == "session" or config.get("scope") == "project":
                default_ttl = config.get("ttl")
                break

        actual_ttl = ttl if ttl is not None else default_ttl
        self.cache.set(key, result, ttl=actual_ttl)

        if self.verbose:
            print(f"    {_c(Colors.DIM, '💾')} Resultado cacheado para '{task_name}'")

    # ── Ejecución principal ──────────────────────────────────────

    def execute(self, plan: ExecutionPlan, filename: str = "<stdin>"):
        """Ejecuta un programa PEX desde un plan validado."""
        self.registry = plan.registry
        self._print_banner(filename)

        # Fase 1: Inicialización de Adaptadores y Caché
        self._print_phase("FASE 1: Inicialización de Adaptadores y Caché")
        self._initialize_adapters()
        self._initialize_cache()

        # Fase 2: Mostrar resumen del programa
        self._print_phase("FASE 2: Modelo del programa (Semántico)")
        self._print_summary()

        # Fase 3: Ejecución de pipelines (si existen)
        if self.registry.pipelines:
            self._print_phase("FASE 3: Ejecución (modo simulación/real)")
            for name, pipeline in self.registry.pipelines.items():
                self._execute_pipeline(pipeline)
        elif self.registry.tasks:
            # Si no hay pipelines, ejecutar tasks individuales
            self._print_phase("FASE 3: Ejecución de tareas (modo simulación/real)")
            for name, task in self.registry.tasks.items():
                self._execute_task(task)

        # Mostrar estadísticas de caché si está habilitada
        if self.use_cache and self.cache:
            self._print_cache_stats()

        self._print_footer()

    def check_only(self, plan: ExecutionPlan, filename: str = "<stdin>"):
        """Solo verifica la sintaxis y estructura del programa."""
        self.registry = plan.registry
        self._print_banner(filename)
        print(_c(Colors.SUCCESS, "  ✓ Sintaxis y semántica correctas"))
        print()

        self._print_summary()
        self._print_footer()

    # ── Inicialización de adaptadores ─────────────────────────────

    def _initialize_adapters(self):
        """Prepara las conexiones LLM y BD en base a tools y models del registro."""
        # Diccionario adicional para adapters MCP
        self.mcp_adapters: Dict[str, Any] = {}

        for name, tool in self.registry.tools.items():
            source = self._resolve_ref(tool.source)

            if tool.provider in ("postgres", "postgresql", "sqlite"):
                try:
                   import pex.adapters as adapt_pkg
                   adapter = adapt_pkg.get_db_adapter(tool.provider, source)
                   if adapter:
                       self.db_adapters[name] = adapter
                       self._log_register("adapter", f"[DB] {tool.provider}")
                except ImportError:
                   pass
            elif tool.provider in ("csv", "json", "txt"):
                try:
                   import pex.adapters as adapt_pkg
                   adapter = adapt_pkg.get_file_adapter(tool.provider, source)
                   if adapter:
                       self.file_adapters[name] = adapter
                       self._log_register("adapter", f"[FILE] {tool.provider}")
                except ImportError:
                   pass
            elif tool.provider == "mcp":
                # MCP tool adapter
                try:
                    import pex.adapters as adapt_pkg
                    # source puede ser "url" o "url:type" (ej: "http://localhost:8080:tool")
                    if ":" in source and not source.startswith("http"):
                        parts = source.split(":")
                        server_url = parts[0]
                        adapter_type = parts[1] if len(parts) > 1 else "tool"
                    else:
                        server_url = source
                        adapter_type = "tool"

                    adapter = adapt_pkg.get_mcp_adapter(adapter_type, server_url, name)
                    if adapter:
                        self.mcp_adapters[name] = adapter
                        self._log_register("adapter", f"[MCP {adapter_type.upper()}] {server_url}")
                except ImportError:
                    pass

        for name, model in self.registry.models.items():
            model_name = self._resolve_ref(model.model_name)
            try:
                import pex.adapters as adapt_pkg

                # Soporte para modelos MCP
                if model.provider == "mcp":
                    adapter = adapt_pkg.get_mcp_adapter("llm", model_name, name)
                    if adapter:
                        self.llm_adapters[name] = adapter
                        self._log_register("adapter", f"[MCP LLM] {model_name}")
                else:
                    adapter = adapt_pkg.get_llm_adapter(model.provider, model_name)
                    if adapter:
                        self.llm_adapters[name] = adapter
                        self._log_register("adapter", f"[LLM] {model.provider} {model_name}")
            except ImportError:
                pass

    def _log_register(self, kind: str, name: str):
        if self.verbose:
            icon = {
                "project": "📦", "task": "📋", "agent": "🤖",
                "pipeline": "🔗", "tool": "🔧", "model": "🧠",
                "memory": "💾", "record": "📄", "entity": "🏷️",
                "var": "📌", "adapter": "🔌"
            }.get(kind, "•")
            print(f"  {icon} Registrado {_c(Colors.CYAN, kind)}: {_c(Colors.WHITE, name)}")

    # ── Ejecución simulada ───────────────────────────────────────

    def _execute_pipeline(self, pipeline: PipelineBlock):
        """Ejecuta un pipeline paso a paso (simulación)."""
        print()
        print(f"  {_c(Colors.HEADER, '🔗 Pipeline')}: {_c(Colors.WHITE, pipeline.name)}")
        print(f"  {'─' * 50}")

        for i, step_name in enumerate(pipeline.steps, 1):
            step_name_str = self._resolve_ref(step_name)
            print(f"  {_c(Colors.DIM, f'  Paso {i}')}: {_c(Colors.YELLOW, step_name_str)}")

            # Buscar referencia: puede ser un task o un agent
            if step_name_str in self.registry.tasks:
                self._execute_task(self.registry.tasks[step_name_str], indent=6)
            elif step_name_str in self.registry.agents:
                self._execute_agent(self.registry.agents[step_name_str], indent=6)
            else:
                print(f"      {_c(Colors.WARN, '⚠')} Referencia no encontrada: {step_name_str}")

        print(f"\n  {_c(Colors.SUCCESS, '✓')} Pipeline '{pipeline.name}' completado (simulación)")

    def _execute_task(self, task: TaskBlock, indent: int = 4):
        """Ejecuta una tarea, usando conectores reales si existen, o simulando si fallan."""
        pad = " " * indent
        print(f"{pad}{_c(Colors.INFO, '📋 Task')}: {_c(Colors.WHITE, task.name)}")

        # 1. Recolectar Inputs
        task_inputs = {}
        if task.inputs:
            for inp in task.inputs:
                resolved = self._resolve_ref(inp)
                # Buscar si el input proviene del output de otra tarea y existe en memoria
                if resolved in self.results:
                    task_inputs[resolved] = self.results[resolved]
                    print(f"{pad}  input: {_c(Colors.CYAN, resolved)} (usando dataset en memoria)")
                else:
                    task_inputs[resolved] = f"[Ref: {resolved}]"
                    print(f"{pad}  input: {_c(Colors.DIM, resolved)}")

        # 2. Recolectar Contexto
        task_ctx = {}
        if task.contexts:
            for ctx in task.contexts:
                resolved_ctx = self._resolve_ref(ctx)
                if resolved_ctx in self.registry.variables:
                    task_ctx[resolved_ctx] = self.registry.variables[resolved_ctx]
                val_str = str(task_ctx.get(resolved_ctx, '?'))
                print(f"{pad}  context: {_c(Colors.DIM, str(resolved_ctx))} [{val_str}]")

        if task.uses:
            for use in task.uses:
                u_name = self._resolve_ref(use)
                print(f"{pad}  use: {_c(Colors.DIM, u_name)}")
        if task.model:
            m_name = self._resolve_ref(task.model)
            print(f"{pad}  model: {_c(Colors.MAGENTA, m_name)}")

        # 3. Intentar obtener de caché ANTES de ejecutar
        if self.use_cache and self.cache:
            cached_result = self._get_from_cache(task.name, task_inputs, task_ctx)
            if cached_result is not None:
                # Cache HIT - usar resultado cacheado
                final_output = cached_result
                if task.output:
                    out_name = task.output.name if hasattr(task.output, "name") else str(task.output)
                    print(f"{pad}  output → {_c(Colors.CYAN, out_name)} (desde caché)")
                    self.results[out_name] = final_output
                print(f"{pad}  {_c(Colors.SUCCESS, '✓')} Tarea procesada (desde caché)")
                print()
                return

        final_output = None

        # 3. Ejecutar QUERY de Archivo si hay
        if task.query:
            query_val = task.query.value if hasattr(task.query, "value") else str(task.query)
            print(f"{pad}  query: {_c(Colors.DIM, query_val[:60])}...")
            
            file_source_name = task.inputs[0] if task.inputs else None
            file_source_name = self._resolve_ref(file_source_name) if file_source_name else ""
            
            if file_source_name in self.file_adapters and self.file_adapters[file_source_name].is_configured:
                print(f"{pad}  {_c(Colors.YELLOW, '⚙ Cargando archivo local...')} desde {file_source_name}")
                adapter = self.file_adapters[file_source_name]
                final_output = adapter.execute_query(query_val)
                
                if isinstance(final_output, list):
                    print(f"{pad}    {_c(Colors.SUCCESS, '✓')} Filas obtenidas: {len(final_output)}")
                elif isinstance(final_output, dict):
                    print(f"{pad}    {_c(Colors.SUCCESS, '✓')} Objeto JSON cargado")
                else:
                    print(f"{pad}    {_c(Colors.SUCCESS, '✓')} Texto cargado: {len(str(final_output))} caracteres")
                
                task_inputs[file_source_name] = final_output
            else:
                 print(f"{pad}  {_c(Colors.WARN, '⚠')} Lector de archivo simulado.")
                 if not final_output: final_output = f"[Contenido de archivo simulado de {task.name}]"

        # 4. Ejecutar SQL si hay
        if task.sql:
            sql_val = task.sql.value if hasattr(task.sql, "value") else str(task.sql)
            print(f"{pad}  sql: {_c(Colors.DIM, sql_val[:60].replace(chr(10), ' '))}...")
            
            db_source_name = task.inputs[0] if task.inputs else None  # Por convención, primer input es la db_tool
            db_source_name = self._resolve_ref(db_source_name) if db_source_name else ""
            
            if db_source_name in self.db_adapters and self.db_adapters[db_source_name].is_configured:
                 print(f"{pad}  {_c(Colors.YELLOW, '⚙ Ejecutando SQL real...')} en {db_source_name}")
                 adapter = self.db_adapters[db_source_name]
                 final_output = adapter.execute_query(sql_val)
                 print(f"{pad}    {_c(Colors.SUCCESS, '✓')} Filas obtenidas: {len(final_output) if isinstance(final_output, list) else 1}")                 
                 task_inputs[db_source_name] = final_output
            else:
                 print(f"{pad}  {_c(Colors.WARN, '⚠')} Base de datos simulada.")
                 final_output = f"[Dataset SQL simulado de {task.name}]"

        # 5. Solucionar el GOAL usando LLM si hay
        if task.goal:
            goal_val = task.goal.value if hasattr(task.goal, "value") else str(task.goal)
            print(f"{pad}  {_c(Colors.GREEN, 'goal')}: {goal_val}")
            
            model_name = task.model.name if hasattr(task.model, "name") else str(task.model)
            if model_name and model_name in self.llm_adapters and self.llm_adapters[model_name].is_configured:
                print(f"{pad}  {_c(Colors.MAGENTA, '✨ Solicitando al modelo LLM real...')} ({model_name})")
                
                adapter = self.llm_adapters[model_name]
                # Enviar los inputs y contextos acumulados al adaptador LLM
                final_output = adapter.execute_intent(goal_val, task_inputs, task_ctx)
                
                # Mostrar el snippet del resultado generado
                snippet = str(final_output).replace('\n', ' ')[:80] + "..."
                print(f"{pad}    {_c(Colors.SUCCESS, '✓ Output AI:')} {_c(Colors.DIM, snippet)}")
            else:
                if not final_output:
                    final_output = f"[Simulación del Goal: {task.name}]"
                print(f"{pad}  {_c(Colors.WARN, '⚠')} Goal simulado. Sin LLM real detectado.")

        # Guardar el estado de finalizacion de variable
        if task.output:
            out_name = task.output.name if hasattr(task.output, "name") else str(task.output)
            print(f"{pad}  output → {_c(Colors.CYAN, out_name)}")
            self.results[out_name] = final_output

            # Guardar en caché si está habilitada
            if self.use_cache and self.cache:
                self._set_in_cache(task.name, task_inputs, task_ctx, final_output)

        print(f"{pad}  {_c(Colors.SUCCESS, '✓')} Tarea procesada")
        print()

    def _execute_agent(self, agent: AgentBlock, indent: int = 4):
        """Simula la ejecución de un agent."""
        pad = " " * indent
        print(f"{pad}{_c(Colors.INFO, '🤖 Agent')}: {_c(Colors.WHITE, agent.name)}")

        if agent.model:
            m_name = self._resolve_ref(agent.model)
            print(f"{pad}  model: {_c(Colors.MAGENTA, m_name)}")
        if agent.uses:
            for use in agent.uses:
                u_name = self._resolve_ref(use)
                print(f"{pad}  use: {_c(Colors.DIM, u_name)}")
        if agent.goal:
            g_val = agent.goal.value if hasattr(agent.goal, "value") else str(agent.goal)
            print(f"{pad}  {_c(Colors.GREEN, 'goal')}: {g_val}")

        print(f"{pad}  {_c(Colors.SUCCESS, '✓')} Agente ejecutado (simulación)")
        print()

    # ── Salida formateada ────────────────────────────────────────

    def _print_banner(self, filename: str):
        print()
        print(_c(Colors.HEADER, "  ╔══════════════════════════════════════════════╗"))
        print(_c(Colors.HEADER, "  ║") + _c(Colors.WHITE, "        PEX Runtime v0.2 — Dry Run            ") + _c(Colors.HEADER, "║"))
        print(_c(Colors.HEADER, "  ╚══════════════════════════════════════════════╝"))
        print(f"  Archivo: {_c(Colors.CYAN, filename)}")
        print()

    def _print_phase(self, title: str):
        print()
        print(f"  {_c(Colors.LABEL, f'── {title} ──')}")

    def _print_summary(self):
        """Imprime un resumen de todo lo registrado."""
        print()
        if self.registry.project:
            print(f"  📦 Proyecto: {_c(Colors.WHITE, self.registry.project.name)}")
            if self.registry.project.imports:
                imps = [i.value if hasattr(i, "value") else str(i) for i in self.registry.project.imports]
                print(f"     imports: {', '.join(imps)}")

        counts = [
            ("📋 Tasks", len(self.registry.tasks)),
            ("🤖 Agents", len(self.registry.agents)),
            ("🔗 Pipelines", len(self.registry.pipelines)),
            ("🔧 Tools", len(self.registry.tools)),
            ("🧠 Models", len(self.registry.models)),
            ("💾 Memory", len(self.registry.memories)),
            ("📄 Records", len(self.registry.records)),
            ("🏷️  Entities", len(self.registry.entities)),
            ("📌 Variables", len(self.registry.variables)),
        ]

        parts = [f"{icon}: {_c(Colors.WHITE, str(count))}" for icon, count in counts if count > 0]
        if parts:
            print(f"  {' │ '.join(parts)}")

    def _print_cache_stats(self):
        """Imprime estadísticas de la caché."""
        if not self.cache:
            return

        stats = self.cache.stats()
        print()
        print(f"  {_c(Colors.LABEL, '── Caché Statistics ──')}")
        print(f"  Hits: {_c(Colors.SUCCESS, str(stats['hits']))} | Misses: {_c(Colors.WARN, str(stats['misses']))} | Hit Rate: {_c(Colors.CYAN, stats['hit_rate'])}")
        print(f"  Entradas cacheadas: {_c(Colors.WHITE, str(stats['size']))}")

    def _print_footer(self):
        print()
        print(_c(Colors.DIM, "  ─────────────────────────────────────────────────"))
        print(_c(Colors.DIM, "  PEX — Programs intention, not implementation."))
        print()
