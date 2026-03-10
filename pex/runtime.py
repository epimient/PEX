"""
PEX Runtime — Motor de ejecución del lenguaje PEX.

Recorre el AST y ejecuta cada bloque. En v0.1 opera en modo
"dry-run": simula la ejecución mostrando las intenciones y
la estructura del programa de forma clara.
"""

import os
from typing import Dict, Any, Optional
from pex.ast_nodes import (
    Program, ProjectBlock, TaskBlock, AgentBlock, PipelineBlock,
    ToolBlock, ModelBlock, MemoryBlock, RecordBlock, EntityBlock,
    Assignment, Comment, StringLiteral, NumberLiteral, BooleanLiteral,
    EnvVarRef, IdentRef,
)


# ─── Colores ANSI para la terminal ───────────────────────────────

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colores
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"
    WHITE = "\033[97m"

    # Combinaciones
    HEADER = "\033[1;36m"
    SUCCESS = "\033[1;32m"
    WARN = "\033[1;33m"
    INFO = "\033[1;34m"
    LABEL = "\033[1;35m"


def _c(color: str, text: str) -> str:
    return f"{color}{text}{Colors.RESET}"


# ─── Runtime ─────────────────────────────────────────────────────

class PexRuntime:
    """Motor de ejecución para programas PEX v0.1 con Adapters Reales."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # Tablas de símbolos base
        self.variables: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskBlock] = {}
        self.agents: Dict[str, AgentBlock] = {}
        self.pipelines: Dict[str, PipelineBlock] = {}
        self.tools: Dict[str, ToolBlock] = {}
        self.models: Dict[str, ModelBlock] = {}
        self.memories: Dict[str, MemoryBlock] = {}
        self.records: Dict[str, RecordBlock] = {}
        self.entities: Dict[str, EntityBlock] = {}
        self.project: Optional[ProjectBlock] = None

        # Instancias de Adaptadores vivos
        self.llm_adapters: Dict[str, Any] = {}
        self.db_adapters: Dict[str, Any] = {}
        self.file_adapters: Dict[str, Any] = {}

        # Resultados de ejecución (estado del sistema)
        self.results: Dict[str, Any] = {}

    # ── Resolución de valores ────────────────────────────────────

    def _resolve_env(self, name: str) -> str:
        """Resuelve $VARIABLE desde el entorno."""
        val = os.environ.get(name, "")
        if not val:
            return f"$({name} no definida)"
        return val

    def _resolve_value(self, val) -> Any:
        """Resuelve un valor del AST a su representación Python."""
        if isinstance(val, StringLiteral):
            return val.value
        elif isinstance(val, NumberLiteral):
            return val.value
        elif isinstance(val, BooleanLiteral):
            return val.value
        elif isinstance(val, EnvVarRef):
            return self._resolve_env(val.name)
        elif isinstance(val, IdentRef):
            # Buscar en variables
            return self.variables.get(val.name, val.name)
        return str(val) if val else ""

    def _resolve_ref(self, ref: str) -> str:
        """Resuelve una referencia que puede ser $VAR o nombre directo."""
        if ref and ref.startswith("$"):
            return self._resolve_env(ref[1:])
        return ref

    # ── Ejecución principal ──────────────────────────────────────

    def execute(self, program: Program):
        """Ejecuta un programa PEX completo."""
        self._print_banner(program.filename)

        # Fase 1: Registrar todos los bloques
        self._print_phase("FASE 1: Análisis semántico")
        for stmt in program.statements:
            self._register(stmt)

        # Fase 2: Mostrar resumen del programa
        self._print_phase("FASE 2: Modelo del programa")
        self._print_summary()

        # Fase 3: Ejecutar pipelines (si existen)
        if self.pipelines:
            self._print_phase("FASE 3: Ejecución (modo simulación)")
            for name, pipeline in self.pipelines.items():
                self._execute_pipeline(pipeline)
        elif self.tasks:
            # Si no hay pipelines, ejecutar tasks individuales
            self._print_phase("FASE 3: Ejecución de tareas (modo simulación)")
            for name, task in self.tasks.items():
                self._execute_task(task)

        self._print_footer()

    def check_only(self, program: Program):
        """Solo verifica la sintaxis y estructura del programa."""
        self._print_banner(program.filename)
        print(_c(Colors.SUCCESS, "  ✓ Sintaxis correcta"))
        print()

        for stmt in program.statements:
            self._register(stmt)

        self._print_summary()
        self._print_footer()

    # ── Registro de bloques ──────────────────────────────────────

    def _register(self, stmt):
        """Registra un bloque en la tabla de símbolos correspondiente."""
        if isinstance(stmt, ProjectBlock):
            self.project = stmt
            self._log_register("project", stmt.name)
        elif isinstance(stmt, TaskBlock):
            self.tasks[stmt.name] = stmt
            self._log_register("task", stmt.name)
        elif isinstance(stmt, AgentBlock):
            self.agents[stmt.name] = stmt
            self._log_register("agent", stmt.name)
        elif isinstance(stmt, PipelineBlock):
            self.pipelines[stmt.name] = stmt
            self._log_register("pipeline", stmt.name)
        elif isinstance(stmt, ToolBlock):
            self.tools[stmt.name] = stmt
            self._log_register("tool", stmt.name)
            # Intentar instanciar adaptador BD
            source = self._resolve_ref(stmt.source)
            if stmt.provider in ("postgres", "postgresql", "sqlite"):
               import pex.adapters as adapt_pkg
               adapter = adapt_pkg.get_db_adapter(stmt.provider, source)
               if adapter:
                   self.db_adapters[stmt.name] = adapter
                   self._log_register("adapter", f"[DB] {stmt.provider}")
            elif stmt.provider in ("csv", "json", "txt"):
               import pex.adapters as adapt_pkg
               adapter = adapt_pkg.get_file_adapter(stmt.provider, source)
               if adapter:
                   self.file_adapters[stmt.name] = adapter
                   self._log_register("adapter", f"[FILE] {stmt.provider}")

        elif isinstance(stmt, ModelBlock):
            self.models[stmt.name] = stmt
            self._log_register("model", stmt.name)
            # Intentar instanciar adaptador LLM
            model_name = self._resolve_ref(stmt.model_name)
            import pex.adapters as adapt_pkg
            adapter = adapt_pkg.get_llm_adapter(stmt.provider, model_name)
            if adapter:
                self.llm_adapters[stmt.name] = adapter
                self._log_register("adapter", f"[LLM] {stmt.provider} {model_name}")
        elif isinstance(stmt, MemoryBlock):
            self.memories[stmt.name] = stmt
            self._log_register("memory", stmt.name)
        elif isinstance(stmt, RecordBlock):
            self.records[stmt.name] = stmt
            self._log_register("record", stmt.name)
        elif isinstance(stmt, EntityBlock):
            self.entities[stmt.name] = stmt
            self._log_register("entity", stmt.name)
        elif isinstance(stmt, Assignment):
            self.variables[stmt.name] = self._resolve_value(stmt.value)
            self._log_register("var", f"{stmt.name} = {self.variables[stmt.name]}")
        elif isinstance(stmt, Comment):
            pass  # Los comentarios no se registran

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
            print(f"  {_c(Colors.DIM, f'  Paso {i}')}: {_c(Colors.YELLOW, step_name)}")

            # Buscar referencia: puede ser un task o un agent
            if step_name in self.tasks:
                self._execute_task(self.tasks[step_name], indent=6)
            elif step_name in self.agents:
                self._execute_agent(self.agents[step_name], indent=6)
            else:
                print(f"      {_c(Colors.WARN, '⚠')} Referencia no encontrada: {step_name}")

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
                if resolved_ctx in self.variables:
                    task_ctx[resolved_ctx] = self.variables[resolved_ctx]
                print(f"{pad}  context: {_c(Colors.DIM, ctx)} [{task_ctx.get(resolved_ctx, '?')}]")

        if task.uses:
            for use in task.uses:
                print(f"{pad}  use: {_c(Colors.DIM, use)}")
        if task.model:
            print(f"{pad}  model: {_c(Colors.MAGENTA, task.model)}")
            
        final_output = None

        # 3. Ejecutar QUERY de Archivo si hay
        if task.query:
            print(f"{pad}  query: {_c(Colors.DIM, task.query[:60])}...")
            
            file_source_name = task.inputs[0] if task.inputs else None
            file_source_name = self._resolve_ref(file_source_name) if file_source_name else ""
            
            if file_source_name in self.file_adapters and self.file_adapters[file_source_name].is_configured:
                print(f"{pad}  {_c(Colors.YELLOW, '⚙ Cargando archivo local...')} desde {file_source_name}")
                adapter = self.file_adapters[file_source_name]
                final_output = adapter.execute_query(task.query)
                
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
            print(f"{pad}  sql: {_c(Colors.DIM, task.sql[:60].replace(chr(10), ' '))}...")
            
            db_source_name = task.inputs[0] if task.inputs else None  # Por convención, primer input es la db_tool
            db_source_name = self._resolve_ref(db_source_name) if db_source_name else ""
            
            if db_source_name in self.db_adapters and self.db_adapters[db_source_name].is_configured:
                 print(f"{pad}  {_c(Colors.YELLOW, '⚙ Ejecutando SQL real...')} en {db_source_name}")
                 adapter = self.db_adapters[db_source_name]
                 final_output = adapter.execute_query(task.sql)
                 print(f"{pad}    {_c(Colors.SUCCESS, '✓')} Filas obtenidas: {len(final_output) if isinstance(final_output, list) else 1}")                 
                 task_inputs[db_source_name] = final_output
            else:
                 print(f"{pad}  {_c(Colors.WARN, '⚠')} Base de datos simulada.")
                 final_output = f"[Dataset SQL simulado de {task.name}]"

        # 5. Solucionar el GOAL usando LLM si hay
        if task.goal:
            print(f"{pad}  {_c(Colors.GREEN, 'goal')}: {task.goal}")
            
            if task.model and task.model in self.llm_adapters and self.llm_adapters[task.model].is_configured:
                print(f"{pad}  {_c(Colors.MAGENTA, '✨ Solicitando al modelo LLM real...')} ({task.model})")
                
                adapter = self.llm_adapters[task.model]
                # Enviar los inputs y contextos acumulados al adaptador LLM
                final_output = adapter.execute_intent(task.goal, task_inputs, task_ctx)
                
                # Mostrar el snippet del resultado generado
                snippet = str(final_output).replace('\n', ' ')[:80] + "..."
                print(f"{pad}    {_c(Colors.SUCCESS, '✓ Output AI:')} {_c(Colors.DIM, snippet)}")
            else:
                if not final_output:
                    final_output = f"[Simulación del Goal: {task.name}]"
                print(f"{pad}  {_c(Colors.WARN, '⚠')} Goal simulado. Sin LLM real detectado.")

        # Guardar el estado de finalizacion de variable
        if task.output:
            print(f"{pad}  output → {_c(Colors.CYAN, task.output)}")
            self.results[task.output] = final_output

        print(f"{pad}  {_c(Colors.SUCCESS, '✓')} Tarea procesada")
        print()

    def _execute_agent(self, agent: AgentBlock, indent: int = 4):
        """Simula la ejecución de un agent."""
        pad = " " * indent
        print(f"{pad}{_c(Colors.INFO, '🤖 Agent')}: {_c(Colors.WHITE, agent.name)}")

        if agent.model:
            print(f"{pad}  model: {_c(Colors.MAGENTA, agent.model)}")
        if agent.uses:
            for use in agent.uses:
                print(f"{pad}  use: {_c(Colors.DIM, use)}")
        if agent.goal:
            print(f"{pad}  {_c(Colors.GREEN, 'goal')}: {agent.goal}")

        print(f"{pad}  {_c(Colors.SUCCESS, '✓')} Agente ejecutado (simulación)")
        print()

    # ── Salida formateada ────────────────────────────────────────

    def _print_banner(self, filename: str):
        print()
        print(_c(Colors.HEADER, "  ╔══════════════════════════════════════════════╗"))
        print(_c(Colors.HEADER, "  ║") + _c(Colors.WHITE, "        PEX Runtime v0.1 — Dry Run            ") + _c(Colors.HEADER, "║"))
        print(_c(Colors.HEADER, "  ╚══════════════════════════════════════════════╝"))
        print(f"  Archivo: {_c(Colors.CYAN, filename)}")
        print()

    def _print_phase(self, title: str):
        print()
        print(f"  {_c(Colors.LABEL, f'── {title} ──')}")

    def _print_summary(self):
        """Imprime un resumen de todo lo registrado."""
        print()
        if self.project:
            print(f"  📦 Proyecto: {_c(Colors.WHITE, self.project.name)}")
            if self.project.imports:
                print(f"     imports: {', '.join(self.project.imports)}")

        counts = [
            ("📋 Tasks", len(self.tasks)),
            ("🤖 Agents", len(self.agents)),
            ("🔗 Pipelines", len(self.pipelines)),
            ("🔧 Tools", len(self.tools)),
            ("🧠 Models", len(self.models)),
            ("💾 Memory", len(self.memories)),
            ("📄 Records", len(self.records)),
            ("🏷️  Entities", len(self.entities)),
            ("📌 Variables", len(self.variables)),
        ]

        parts = [f"{icon}: {_c(Colors.WHITE, str(count))}" for icon, count in counts if count > 0]
        if parts:
            print(f"  {' │ '.join(parts)}")

    def _print_footer(self):
        print()
        print(_c(Colors.DIM, "  ─────────────────────────────────────────────────"))
        print(_c(Colors.DIM, "  PEX — Programs intention, not implementation."))
        print()
