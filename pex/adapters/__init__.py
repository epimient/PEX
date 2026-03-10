"""
PEX Adapters — Sistema de plugins para LLMs y Bases de Datos.

Define las interfaces base y provee funciones de factoría
para obtener el adaptador correcto según el proveedor.
"""

from typing import Optional, Dict, Any, List


class LLMAdapter:
    """Interfaz base para modelos de lenguaje."""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.is_configured = False

    def execute_intent(self, goal: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Ejecuta una intención (task/agent) en base a un goal, entradas y contexto.
        Debe retornar el resultado generado por el modelo.
        """
        raise NotImplementedError("LLMAdapter debe implementar execute_intent()")


class DBAdapter:
    """Interfaz base para bases de datos."""
    
    def __init__(self, source_url: str):
        self.source_url = source_url
        self.is_configured = False

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y retorna los registros como una lista de diccionarios.
        """
        raise NotImplementedError("DBAdapter debe implementar execute_query()")


# ─── Factorías de adaptadores ────────────────────────────────────

def get_llm_adapter(provider: str, model_name: str, **kwargs) -> Optional[LLMAdapter]:
    """Retorna la instancia del adaptador LLM según el proveedor."""
    provider = provider.lower() if provider else ""
    
    if provider == "openai":
        try:
            from pex.adapters.llm import OpenAIAdapter
            return OpenAIAdapter(model_name, **kwargs)
        except ImportError:
            print("[Warning] pex/adapters/llm.py no encontrado o faltan dependencias.")
            return None
            
    elif provider == "ollama":
        try:
            from pex.adapters.llm import OllamaAdapter
            return OllamaAdapter(model_name, **kwargs)
        except ImportError:
            print("[Warning] ollama adapter failed to load (falta modulo requests).")
            return None
            
    return None


def get_db_adapter(provider: str, source_url: str) -> Optional[DBAdapter]:
    """Retorna la instancia del adaptador de Base de Datos según el proveedor."""
    provider = provider.lower() if provider else ""
    
    if provider == "sqlite":
        try:
            from pex.adapters.db import SQLiteAdapter
            return SQLiteAdapter(source_url)
        except ImportError:
            return None
            
    elif provider == "postgres" or provider == "postgresql":
        try:
            from pex.adapters.db import PostgresAdapter
            return PostgresAdapter(source_url)
        except ImportError:
            return None
            
    return None

def get_file_adapter(provider: str, source_path: str) -> Optional[Any]:
    """Retorna la instancia del adaptador de Archivos según el proveedor."""
    provider = provider.lower() if provider else ""

    if provider in ("csv", "json", "txt", "md"):
        from pex.adapters.file import FileAdapter
        return FileAdapter(source_path, format_type=provider)

    return None


def get_mcp_adapter(adapter_type: str, server_url: str, server_name: str = "mcp"):
    """
    Crea un adapter MCP según el tipo.

    Args:
        adapter_type: Tipo de adapter ("tool", "resource", "prompt", "llm")
        server_url: URL del servidor MCP
        server_name: Nombre del servidor

    Returns:
        Instancia del adapter MCP o None
    """
    try:
        from pex.adapters.mcp import (
            get_mcp_tool_adapter,
            get_mcp_resource_adapter,
            get_mcp_prompt_adapter,
            MCPLLMAdapter
        )

        adapter_type = adapter_type.lower() if adapter_type else ""

        if adapter_type == "tool":
            return get_mcp_tool_adapter(server_url, server_name)
        elif adapter_type == "resource":
            return get_mcp_resource_adapter(server_url, server_name)
        elif adapter_type == "prompt":
            return get_mcp_prompt_adapter(server_url, server_name)
        elif adapter_type == "llm":
            return MCPLLMAdapter(server_url, server_name)
        else:
            return None

    except ImportError:
        return None
