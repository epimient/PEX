"""
PEX Diagnostics — Sistema unificado de diagnósticos para el lenguaje PEX.

Proporciona una estructura común para errores, advertencias e información,
permitiendo mensajes consistentes, formateo bonito y futura integración con LSP.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class DiagnosticKind(Enum):
    """Tipo de diagnóstico."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


# ═══════════════════════════════════════════════════════════════════
# Códigos de Error Oficiales PEX v0.3
# ═══════════════════════════════════════════════════════════════════

class ErrorCode:
    """Códigos de error oficiales del lenguaje PEX."""
    
    # Errores Léxicos (L001-L099)
    L001 = "L001"  # Cadena literal sin cerrar
    L002 = "L002"  # Bloque multilínea sin cerrar
    L003 = "L003"  # Indentación inconsistente
    L004 = "L004"  # Carácter inesperado
    
    # Errores de Sintaxis (S001-S099)
    S001 = "S001"  # Token inesperado
    S002 = "S002"  # Se esperaba keyword
    S003 = "S003"  # Bloque vacío inválido
    
    # Errores Semánticos (E001-E099)
    E001 = "E001"  # Nombre duplicado (task/agent/tool/model)
    E002 = "E002"  # Referencia no encontrada (input/output/step)
    E003 = "E003"  # Import no existe
    E004 = "E004"  # Ciclo de imports detectado
    E005 = "E005"  # Input/output no declarado
    E006 = "E006"  # Tool no declarada en task/agent
    E007 = "E007"  # Model no declarado en task/agent
    E008 = "E008"  # Step en pipeline no es task ni agent
    E009 = "E009"  # Output usado antes de ser definido en pipeline
    
    # Advertencias (W001-W099)
    W001 = "W001"  # Variable no usada
    W002 = "W002"  # Import no usado
    W003 = "W003"  # Task sin output declarado
    W004 = "W004"  # Model sin provider explícito
    
    # Información (I001-I099)
    I001 = "I001"  # Archivo procesado exitosamente
    I002 = "I002"  # Import resuelto


@dataclass
class Diagnostic:
    """
    Representa un diagnóstico (error, warning, info) en el compilador PEX.
    
    Attributes:
        kind: Tipo de diagnóstico (error, warning, info, hint)
        code: Código oficial del error (ej: "E001")
        message: Mensaje descriptivo del problema
        file: Archivo donde ocurrió el problema
        line: Línea donde ocurrió (1-based)
        column: Columna opcional donde ocurrió
        hint: Sugerencia opcional para resolver el problema
        context: Línea de código relevante (opcional)
    """
    kind: DiagnosticKind
    code: str
    message: str
    file: str
    line: int
    column: Optional[int] = None
    hint: Optional[str] = None
    context: Optional[str] = None
    
    def __post_init__(self):
        """Validar que el código tenga formato correcto."""
        if not self.code or len(self.code) < 3:
            raise ValueError(f"Código de diagnóstico inválido: {self.code}")
    
    def format(self, use_colors: bool = True) -> str:
        """
        Formatea el diagnóstico para mostrar en CLI.
        
        Args:
            use_colors: Si True, usa códigos ANSI para colores.
        
        Returns:
            String formateado listo para imprimir.
        """
        from pex.cli import Colors
        
        # Colores según tipo
        color_map = {
            DiagnosticKind.ERROR: Colors.RED,
            DiagnosticKind.WARNING: Colors.YELLOW,
            DiagnosticKind.INFO: Colors.CYAN,
            DiagnosticKind.HINT: Colors.DIM,
        }
        
        icon_map = {
            DiagnosticKind.ERROR: "✗",
            DiagnosticKind.WARNING: "⚠",
            DiagnosticKind.INFO: "ℹ",
            DiagnosticKind.HINT: "→",
        }
        
        kind_color = color_map.get(self.kind, Colors.WHITE)
        icon = icon_map.get(self.kind, "•")
        
        # Construir mensaje principal
        parts = []
        
        # Línea 1: Icono + Tipo + Código + Mensaje
        header = f"  {icon} "
        if use_colors:
            header += f"{kind_color}[{self.kind.value.upper()}]{Colors.RESET} "
            header += f"{Colors.DIM}{self.code}{Colors.RESET}: "
        else:
            header += f"[{self.kind.value.upper()}] {self.code}: "
        
        header += self.message
        parts.append(header)
        
        # Línea 2: Archivo y línea
        location = f"     📍 {self.file}"
        if self.line > 0:
            location += f":{self.line}"
            if self.column is not None and self.column > 0:
                location += f":{self.column}"
        parts.append(location)
        
        # Línea 3: Contexto (código fuente) si está disponible
        if self.context:
            parts.append(f"     {Colors.DIM}│{Colors.RESET}")
            parts.append(f"     {Colors.DIM}{self.line:4} │{Colors.RESET} {self.context.strip()}")
            parts.append(f"     {Colors.DIM}│{Colors.RESET}")
        
        # Línea 4: Hint si está disponible
        if self.hint:
            parts.append(f"     {Colors.DIM}💡 Sugerencia: {self.hint}{Colors.RESET}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> dict:
        """Convierte el diagnóstico a un diccionario serializable."""
        return {
            "kind": self.kind.value,
            "code": self.code,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "hint": self.hint,
            "context": self.context,
        }


@dataclass
class DiagnosticCollection:
    """
    Colección de diagnósticos acumulados durante la compilación.
    
    Permite acumular múltiples errores antes de fallar, proporcionando
    mejor experiencia de desarrollo.
    """
    diagnostics: List[Diagnostic] = field(default_factory=list)
    
    def add(self, diagnostic: Diagnostic):
        """Agrega un diagnóstico a la colección."""
        self.diagnostics.append(diagnostic)
    
    def has_errors(self) -> bool:
        """Retorna True si hay al menos un error."""
        return any(d.kind == DiagnosticKind.ERROR for d in self.diagnostics)
    
    def has_warnings(self) -> bool:
        """Retorna True si hay al menos una advertencia."""
        return any(d.kind == DiagnosticKind.WARNING for d in self.diagnostics)
    
    def errors(self) -> List[Diagnostic]:
        """Retorna solo los errores."""
        return [d for d in self.diagnostics if d.kind == DiagnosticKind.ERROR]
    
    def warnings(self) -> List[Diagnostic]:
        """Retorna solo las advertencias."""
        return [d for d in self.diagnostics if d.kind == DiagnosticKind.WARNING]
    
    def format_all(self, use_colors: bool = True) -> str:
        """Formatea todos los diagnósticos para mostrar en CLI."""
        if not self.diagnostics:
            return ""
        
        formatted = [d.format(use_colors) for d in self.diagnostics]
        return "\n\n".join(formatted)
    
    def raise_if_errors(self):
        """Lanza DiagnosticError si hay errores."""
        if self.has_errors():
            raise DiagnosticError(self)
    
    def clear(self):
        """Limpia todos los diagnósticos."""
        self.diagnostics.clear()


class DiagnosticError(Exception):
    """
    Excepción que contiene una colección de diagnósticos.
    
    Se usa para propagar errores de compilación manteniendo
    toda la información de diagnóstico disponible.
    """
    def __init__(self, collection: DiagnosticCollection):
        self.collection = collection
        super().__init__(f"{len(collection.errors())} error(s) de compilación")
    
    def format(self, use_colors: bool = True) -> str:
        """Formatea todos los errores para mostrar."""
        return self.collection.format_all(use_colors)


# ═══════════════════════════════════════════════════════════════════
# Helpers para crear diagnósticos comunes
# ═══════════════════════════════════════════════════════════════════

def error_duplicate_name(name: str, kind: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para nombre duplicado."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E001,
        message=f"{kind.capitalize()} duplicada: '{name}'",
        file=file,
        line=line,
        hint=f"Renombra una de las {kind.lower()}s o elimina la definición redundante.",
    )


def error_reference_not_found(ref: str, ref_type: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para referencia no encontrada."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E002,
        message=f"{ref_type.capitalize()} '{ref}' no existe",
        file=file,
        line=line,
        hint=f"Verifica que '{ref}' esté definido como {ref_type.lower()} antes de usarlo.",
    )


def error_import_not_found(module: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para import no encontrado."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E003,
        message=f"Módulo importado '{module}' no se encontró",
        file=file,
        line=line,
        hint=f"Asegúrate de que '{module}.pi' existe en el mismo directorio.",
    )


def error_import_cycle(cycle_path: List[str], file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para ciclo de imports."""
    cycle_str = " → ".join(cycle_path)
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E004,
        message=f"Ciclo de imports detectado: {cycle_str}",
        file=file,
        line=line,
        hint="Reestructura los imports para eliminar el ciclo circular.",
    )


def error_undefined_input(task: str, input_name: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para input no declarado."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E005,
        message=f"Task '{task}' usa input '{input_name}' que no está declarado",
        file=file,
        line=line,
        hint=f"'{input_name}' debe ser un tool, variable, o output de otra task.",
    )


def error_undefined_tool(task: str, tool_name: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para tool no declarada."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E006,
        message=f"Task '{task}' usa tool '{tool_name}' que no está declarada",
        file=file,
        line=line,
        hint=f"Agrega 'tool {tool_name}' con su provider correspondiente.",
    )


def error_undefined_model(task: str, model_name: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para model no declarado."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E007,
        message=f"Task '{task}' usa model '{model_name}' que no está declarado",
        file=file,
        line=line,
        hint=f"Agrega 'model {model_name}' con provider y name.",
    )


def error_undefined_step(pipeline: str, step_name: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para step no encontrado en pipeline."""
    return Diagnostic(
        kind=DiagnosticKind.ERROR,
        code=ErrorCode.E008,
        message=f"Pipeline '{pipeline}' tiene step '{step_name}' que no es task ni agent",
        file=file,
        line=line,
        hint=f"Define '{step_name}' como task o agent antes del pipeline.",
    )


def warning_unused_variable(name: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para variable no usada."""
    return Diagnostic(
        kind=DiagnosticKind.WARNING,
        code=ErrorCode.W001,
        message=f"Variable '{name}' no está siendo usada",
        file=file,
        line=line,
        hint="Considera eliminarla o usarla en una task/pipeline.",
    )


def warning_unused_import(module: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico para import no usado."""
    return Diagnostic(
        kind=DiagnosticKind.WARNING,
        code=ErrorCode.W002,
        message=f"Import '{module}' no está siendo usado",
        file=file,
        line=line,
        hint="Elimina el import si no es necesario.",
    )


def info_file_processed(file: str) -> Diagnostic:
    """Crea un diagnóstico de información para archivo procesado."""
    return Diagnostic(
        kind=DiagnosticKind.INFO,
        code=ErrorCode.I001,
        message=f"Archivo procesado exitosamente: {file}",
        file=file,
        line=0,
    )


def info_import_resolved(module: str, file: str, line: int) -> Diagnostic:
    """Crea un diagnóstico de información para import resuelto."""
    return Diagnostic(
        kind=DiagnosticKind.INFO,
        code=ErrorCode.I002,
        message=f"Import '{module}' resuelto correctamente",
        file=file,
        line=line,
    )
