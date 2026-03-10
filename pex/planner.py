"""
PEX Planner — Validación semántica y planificador de resolución.
"""

from typing import List, Set, Optional
import os
from pex.ast_nodes import Program, IdentRef, ProjectBlock
from pex.registry import Registry
from pex.diagnostics import (
    Diagnostic, DiagnosticKind, DiagnosticCollection, DiagnosticError,
    error_reference_not_found, error_import_not_found, error_import_cycle,
    error_undefined_input, error_undefined_tool, error_undefined_model,
    error_undefined_step, ErrorCode
)


class ExecutionPlan:
    """
    Contiene todo el modelo validado y listo para ejecución.

    Attributes:
        registry: Registro con todos los símbolos del programa.
        project_name: Nombre del proyecto principal.
        diagnostics: Colección de diagnósticos generados durante la planificación.
    """
    def __init__(self, registry: Registry, diagnostics: Optional[DiagnosticCollection] = None):
        self.registry = registry
        self.project_name = registry.project.name if registry.project else "unknown"
        self.diagnostics = diagnostics or registry.diagnostics

    def get_summary(self) -> dict:
        return {
            "project": self.project_name,
            "tasks": len(self.registry.tasks),
            "pipelines": len(self.registry.pipelines),
            "tools": len(self.registry.tools),
            "models": len(self.registry.models),
            "variables": len(self.registry.variables)
        }

    def has_errors(self) -> bool:
        """Retorna True si hay errores en el plan."""
        return self.diagnostics.has_errors()


class ExecutionPlanner:
    """
    Analiza semánticamente el AST, resuelve dependencias/imports
    y genera un ExecutionPlan.

    Attributes:
        registry: Registro global de símbolos.
        visited_files: Archivos ya procesados para evitar ciclos.
        import_stack: Pila de imports actual para detección de ciclos.
        diagnostics: Colección de diagnósticos acumulados.
    """

    def __init__(self, diagnostics: Optional[DiagnosticCollection] = None):
        self.registry = Registry(diagnostics)
        self.visited_files: Set[str] = set()
        self.import_stack: List[str] = []
        self.diagnostics = diagnostics or DiagnosticCollection()

    def build_plan(self, program: Program) -> ExecutionPlan:
        """
        Construye el plan de ejecución validando semánticamente el programa.

        Fases:
        1. Resolve imports recursivamente
        2. Registrar símbolos locales
        3. Validar referencias cruzadas

        Args:
            program: AST del programa parseado.

        Returns:
            ExecutionPlan validado (o con errores acumulados).

        Raises:
            DiagnosticError: Si hay errores críticos que impiden continuar.
        """
        # FASE 0: Parseo recursivo de imports
        self._resolve_imports(program)

        # FASE 1: Registrar símbolos locales
        filename = program.filename if program.filename else "<stdin>"
        for stmt in program.statements:
            self.registry.register(stmt, filename=filename)

        # FASE 2: Validación Semántica Global
        self._validate_cross_references()

        return ExecutionPlan(self.registry, self.diagnostics)

    def _resolve_imports(self, program: Program, depth: int = 0):
        """
        Busca imports en el ProjectBlock y los procesa recursivamente.

        Soporta imports relativos con ../ para navegar directorios.

        Detecta ciclos de imports usando una pila de archivos visitados.

        Args:
            program: Programa a procesar.
            depth: Profundidad actual de imports (para debugging).

        Raises:
            DiagnosticError: Si se detecta un ciclo o import faltante.
        """
        if not program.filename or program.filename == "<stdin>":
            return

        current_path = os.path.abspath(program.filename)

        # Detectar ciclo de imports
        if current_path in self.import_stack:
            cycle_path = self.import_stack + [current_path]
            self.diagnostics.add(error_import_cycle(
                cycle_path=cycle_path,
                file=program.filename,
                line=0,
            ))
            self.diagnostics.raise_if_errors()

        self.import_stack.append(current_path)
        self.visited_files.add(current_path)
        base_dir = os.path.dirname(current_path)

        from pex.parser import parse_file

        for stmt in program.statements:
            if isinstance(stmt, ProjectBlock):
                for imp in stmt.imports:
                    module_name = getattr(imp, "name", getattr(imp, "value", str(imp)))

                    # Soporte para imports relativos
                    if module_name.startswith("../") or module_name.startswith("./"):
                        # Import relativo - resolver desde base_dir
                        target_file = os.path.normpath(
                            os.path.join(base_dir, f"{module_name}.pi")
                        )
                    elif "/" in module_name:
                        # Path relativo directo (ej: modules/tools)
                        target_file = os.path.normpath(
                            os.path.join(base_dir, f"{module_name}.pi")
                        )
                    else:
                        # Import simple del mismo directorio
                        target_file = os.path.join(base_dir, f"{module_name}.pi")

                    if os.path.abspath(target_file) in self.visited_files:
                        # Ya fue procesado, no hay problema
                        continue

                    if not os.path.exists(target_file):
                        self.diagnostics.add(error_import_not_found(
                            module=module_name,
                            file=program.filename,
                            line=stmt.line if hasattr(stmt, 'line') else 0,
                        ))
                        continue  # Continuar con otros imports para acumular errores

                    # Parsear el archivo importado
                    try:
                        imported_program = parse_file(target_file)
                    except Exception as e:
                        # Error al parsear el import
                        self.diagnostics.add(Diagnostic(
                            kind=DiagnosticKind.ERROR,
                            code=ErrorCode.S001,
                            message=f"Error al parsear módulo '{module_name}': {str(e)}",
                            file=target_file,
                            line=0,
                        ))
                        continue

                    # Llamada recursiva por si este módulo importa otros
                    self._resolve_imports(imported_program, depth + 1)

                    # Registrar sus declaraciones EN EL MISMO REGISTRY
                    for imp_stmt in imported_program.statements:
                        if not isinstance(imp_stmt, ProjectBlock):
                            self.registry.register(imp_stmt, filename=target_file)

        # Sacar de la pila al terminar
        self.import_stack.pop()

    def _validate_cross_references(self):
        """
        Valida que todas las referencias cruzadas existan en el modelo semántico.

        Valida:
        1. Steps de pipelines son tasks o agents válidos
        2. Tools usadas en tasks/agents están declaradas
        3. Inputs de tasks están disponibles
        4. Models usados en tasks/agents están declarados

        Los errores se acumulan en self.diagnostics.
        """
        # 1. Validar pipelines
        for pipe_name, pipe in self.registry.pipelines.items():
            for step in pipe.steps:
                s_name = step.name if hasattr(step, "name") else str(step)
                if s_name not in self.registry.tasks and s_name not in self.registry.agents:
                    self.diagnostics.add(error_undefined_step(
                        pipeline=pipe_name,
                        step_name=s_name,
                        file="<unknown>",
                        line=pipe.line if hasattr(pipe, 'line') else 0,
                    ))

        # 2. Validar tools e inputs en tasks
        for t_name, task in self.registry.tasks.items():
            # Validar 'uses' (tools)
            for use in task.uses:
                u_name = use.name if hasattr(use, "name") else str(use)
                if u_name not in self.registry.tools:
                    self.diagnostics.add(error_undefined_tool(
                        task=t_name,
                        tool_name=u_name,
                        file="<unknown>",
                        line=task.line if hasattr(task, 'line') else 0,
                    ))

            # Validar 'inputs'
            for inp in task.inputs:
                if isinstance(inp, IdentRef):
                    i_name = inp.name
                    # El input debe ser una herramienta, una variable, o un output registrado de otra task
                    is_valid = (
                        i_name in self.registry.tools or
                        i_name in self.registry.variables or
                        any(t.output == i_name for t in self.registry.tasks.values())
                    )
                    if not is_valid:
                        self.diagnostics.add(error_undefined_input(
                            task=t_name,
                            input_name=i_name,
                            file="<unknown>",
                            line=task.line if hasattr(task, 'line') else 0,
                        ))

            # Validar model
            if task.model:
                m_name = task.model.name if hasattr(task.model, "name") else str(task.model)
                if m_name not in self.registry.models:
                    self.diagnostics.add(error_undefined_model(
                        task=t_name,
                        model_name=m_name,
                        file="<unknown>",
                        line=task.line if hasattr(task, 'line') else 0,
                    ))

        # 3. Validar agents
        for a_name, agent in self.registry.agents.items():
            if agent.model:
                m_name = agent.model.name if hasattr(agent.model, "name") else str(agent.model)
                if m_name not in self.registry.models:
                    self.diagnostics.add(error_undefined_model(
                        task=a_name,
                        model_name=m_name,
                        file="<unknown>",
                        line=agent.line if hasattr(agent, 'line') else 0,
                    ))
            for use in agent.uses:
                u_name = use.name if hasattr(use, "name") else str(use)
                if u_name not in self.registry.tools:
                    self.diagnostics.add(error_undefined_tool(
                        task=a_name,
                        tool_name=u_name,
                        file="<unknown>",
                        line=agent.line if hasattr(agent, 'line') else 0,
                    ))
