"""
PEX AST — Nodos del Árbol Sintáctico Abstracto.

Define todas las estructuras que representan un programa PEX
después del análisis sintáctico (parsing).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ─── Valores literales ────────────────────────────────────────────

@dataclass
class StringLiteral:
    value: str

@dataclass
class NumberLiteral:
    value: float  # también cubre enteros

@dataclass
class BooleanLiteral:
    value: bool

@dataclass
class EnvVarRef:
    """Referencia a variable de entorno: $VARIABLE_NAME"""
    name: str

@dataclass
class IdentRef:
    """Referencia a un identificador (nombre de task, tool, model, etc.)"""
    name: str


# ─── Sentencias de nivel superior ─────────────────────────────────

@dataclass
class Assignment:
    """variable = valor"""
    name: str
    value: Any  # StringLiteral | NumberLiteral | BooleanLiteral | EnvVarRef
    line: int = 0

@dataclass
class Comment:
    text: str
    line: int = 0


# ─── Bloques principales ─────────────────────────────────────────

@dataclass
class ProjectBlock:
    """
    project <name>
       import <module>
    """
    name: str
    imports: List[str] = field(default_factory=list)
    line: int = 0

@dataclass
class TaskBlock:
    """
    task <name>
       input <source>
       context <ctx>
       use <tool>
       model <model>
       goal <text>
       output <ident>
       sql \"\"\"...\"\"\"
       query <text>
    """
    name: str
    inputs: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)
    model: Optional[str] = None
    goal: Optional[str] = None
    output: Optional[str] = None
    sql: Optional[str] = None
    query: Optional[str] = None
    line: int = 0

@dataclass
class AgentBlock:
    """
    agent <name>
       goal <text>
       model <model>
       use <tool>
    """
    name: str
    goal: Optional[str] = None
    model: Optional[str] = None
    uses: List[str] = field(default_factory=list)
    line: int = 0

@dataclass
class PipelineBlock:
    """
    pipeline <name>
       step <task_or_agent>
    """
    name: str
    steps: List[str] = field(default_factory=list)
    line: int = 0

@dataclass
class ToolBlock:
    """
    tool <name>
       provider <provider>
       source <source>
    """
    name: str
    provider: Optional[str] = None
    source: Optional[str] = None
    line: int = 0

@dataclass
class ModelBlock:
    """
    model <name>
       provider <provider>
       name <model_name>
    """
    name: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    line: int = 0

@dataclass
class MemoryBlock:
    """
    memory <name>
       scope <scope>
    """
    name: str
    scope: Optional[str] = None
    line: int = 0

@dataclass
class RecordBlock:
    """
    record <name>
       <field_name>
    """
    name: str
    fields: List[str] = field(default_factory=list)
    line: int = 0

@dataclass
class EntityBlock:
    """
    entity <name>
       table <table_name>
       field <field_name>
    """
    name: str
    table: Optional[str] = None
    fields: List[str] = field(default_factory=list)
    line: int = 0


# ─── Programa completo ───────────────────────────────────────────

@dataclass
class Program:
    """Nodo raíz: contiene todas las sentencias del archivo .pi"""
    statements: List[Any] = field(default_factory=list)
    filename: str = ""
