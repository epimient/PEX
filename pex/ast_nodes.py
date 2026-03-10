"""
PEX AST — Nodos del Árbol Sintáctico Abstracto.

Define todas las estructuras que representan un programa PEX
después del análisis sintáctico (parsing).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


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


# ─── Nodos de Valor ──────────────────────────────────────────────

ValueNode = Union[StringLiteral, NumberLiteral, BooleanLiteral, EnvVarRef, IdentRef]
TextNode = Union[StringLiteral, EnvVarRef, IdentRef]

# ─── Sentencias de nivel superior ─────────────────────────────────

@dataclass
class Assignment:
    """variable = valor"""
    name: str
    value: ValueNode
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
    inputs: List[ValueNode] = field(default_factory=list)
    contexts: List[ValueNode] = field(default_factory=list)
    uses: List[IdentRef] = field(default_factory=list)
    model: Optional[IdentRef] = None
    goal: Optional[TextNode] = None
    output: Optional[str] = None
    sql: Optional[TextNode] = None
    query: Optional[TextNode] = None
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
    goal: Optional[TextNode] = None
    model: Optional[IdentRef] = None
    uses: List[IdentRef] = field(default_factory=list)
    line: int = 0

@dataclass
class PipelineBlock:
    """
    pipeline <name>
       step <task_or_agent>
    """
    name: str
    steps: List[IdentRef] = field(default_factory=list)
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
    source: Optional[ValueNode] = None
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
    model_name: Optional[TextNode] = None
    line: int = 0

@dataclass
class MemoryBlock:
    """
    memory <name>
       scope <scope>
       ttl <seconds>
    """
    name: str
    scope: Optional[str] = None
    ttl: Optional[int] = None  # Time-to-live en segundos (None = sin expiración)
    line: int = 0

@dataclass
class RecordField:
    """Campo de un record con tipo opcional."""
    name: str
    field_type: Optional[str] = None  # None = sin tipo definido (dinámico)


@dataclass
class RecordBlock:
    """
    record <name>
       <field_name> [: <type>]
    """
    name: str
    fields: List[RecordField] = field(default_factory=list)
    line: int = 0

    def add_field(self, name: str, field_type: Optional[str] = None):
        """Agrega un campo al record."""
        self.fields.append(RecordField(name=name, field_type=field_type))


@dataclass
class EntityField:
    """Campo de una entidad con tipo opcional."""
    name: str
    field_type: Optional[str] = None


@dataclass
class EntityBlock:
    """
    entity <name>
       table <table_name>
       field <field_name> [: <type>]
    """
    name: str
    table: Optional[str] = None
    fields: List[EntityField] = field(default_factory=list)
    line: int = 0

    def add_field(self, name: str, field_type: Optional[str] = None):
        """Agrega un campo a la entidad."""
        self.fields.append(EntityField(name=name, field_type=field_type))


Statement = Union[
    Assignment, ProjectBlock, TaskBlock, AgentBlock,
    PipelineBlock, ToolBlock, ModelBlock, MemoryBlock,
    RecordBlock, EntityBlock
]

@dataclass
class Program:
    """Nodo raíz: contiene todas las sentencias del archivo .pi"""
    statements: List[Statement] = field(default_factory=list)
    filename: str = ""
