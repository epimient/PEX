"""
PEX Registry — Tabla de símbolos unificada para el lenguaje.
"""

from typing import Dict, Any, List, Optional
from pex.ast_nodes import (
    ProjectBlock, TaskBlock, AgentBlock, PipelineBlock, ToolBlock,
    ModelBlock, MemoryBlock, RecordBlock, EntityBlock, Assignment
)
from pex.diagnostics import (
    Diagnostic, DiagnosticKind, DiagnosticCollection, DiagnosticError,
    error_duplicate_name, ErrorCode
)


class Registry:
    """
    Almacena el estado global de todos los bloques válidamente parseados
    y componentes semánticos.

    Attributes:
        diagnostics: Colección de diagnósticos acumulados durante el registro.
    """
    def __init__(self, diagnostics: Optional[DiagnosticCollection] = None):
        self.project: Any = None
        self.tasks: Dict[str, TaskBlock] = {}
        self.agents: Dict[str, AgentBlock] = {}
        self.pipelines: Dict[str, PipelineBlock] = {}
        self.tools: Dict[str, ToolBlock] = {}
        self.models: Dict[str, ModelBlock] = {}
        self.memories: Dict[str, MemoryBlock] = {}
        self.records: Dict[str, RecordBlock] = {}
        self.entities: Dict[str, EntityBlock] = {}
        self.variables: Dict[str, Any] = {}
        self.diagnostics = diagnostics or DiagnosticCollection()

    def register(self, stmt: Any, filename: str = "<unknown>"):
        """
        Añade una sentencia (bloque o variable) al registro validando colisiones.

        Args:
            stmt: La sentencia a registrar (TaskBlock, AgentBlock, etc.)
            filename: Archivo donde se definió la sentencia para mejores errores.

        Raises:
            DiagnosticError: Si se detecta una colisión de nombres.
        """
        if isinstance(stmt, ProjectBlock):
            self.project = stmt
        elif isinstance(stmt, Assignment):
            self.variables[stmt.name] = stmt.value.value if hasattr(stmt.value, "value") else str(stmt.value)
        elif isinstance(stmt, TaskBlock):
            if stmt.name in self.tasks:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="task",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.tasks[stmt.name] = stmt
        elif isinstance(stmt, AgentBlock):
            if stmt.name in self.agents:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="agent",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.agents[stmt.name] = stmt
        elif isinstance(stmt, PipelineBlock):
            if stmt.name in self.pipelines:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="pipeline",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.pipelines[stmt.name] = stmt
        elif isinstance(stmt, ToolBlock):
            if stmt.name in self.tools:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="tool",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.tools[stmt.name] = stmt
        elif isinstance(stmt, ModelBlock):
            if stmt.name in self.models:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="model",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.models[stmt.name] = stmt
        elif isinstance(stmt, MemoryBlock):
            if stmt.name in self.memories:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="memory",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.memories[stmt.name] = stmt
        elif isinstance(stmt, RecordBlock):
            if stmt.name in self.records:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="record",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.records[stmt.name] = stmt
        elif isinstance(stmt, EntityBlock):
            if stmt.name in self.entities:
                self.diagnostics.add(error_duplicate_name(
                    name=stmt.name,
                    kind="entity",
                    file=filename,
                    line=stmt.line,
                ))
                self.diagnostics.raise_if_errors()
            self.entities[stmt.name] = stmt

    def clear(self):
        """Limpia todos los registros y diagnósticos."""
        self.project = None
        self.tasks.clear()
        self.agents.clear()
        self.pipelines.clear()
        self.tools.clear()
        self.models.clear()
        self.memories.clear()
        self.records.clear()
        self.entities.clear()
        self.variables.clear()
        self.diagnostics.clear()
