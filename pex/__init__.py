"""
PEX — Lenguaje de programación cognitivo orientado a intención.
PEX programs intention, not implementation.
"""

__version__ = "0.4.0"

# Exportar componentes principales
from pex.diagnostics import (
    Diagnostic,
    DiagnosticKind,
    DiagnosticCollection,
    DiagnosticError,
    ErrorCode,
)

from pex.registry import Registry
from pex.planner import ExecutionPlanner, ExecutionPlan
from pex.runtime import PexRuntime
from pex.cache import Cache, get_global_cache, clear_global_cache

__all__ = [
    # Versión
    "__version__",
    # Diagnósticos
    "Diagnostic",
    "DiagnosticKind",
    "DiagnosticCollection",
    "DiagnosticError",
    "ErrorCode",
    # Componentes principales
    "Registry",
    "ExecutionPlanner",
    "ExecutionPlan",
    "PexRuntime",
    # Caché
    "Cache",
    "get_global_cache",
    "clear_global_cache",
]
