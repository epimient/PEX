"""
PEX MCP Adapter — Integración con Model Context Protocol.

MCP (Model Context Protocol) es un protocolo estandarizado para conectar
modelos de IA con herramientas, recursos y prompts externos.

Documentación: https://modelcontextprotocol.io/
"""

import os
import json
import time
from typing import Optional, Dict, Any, List

# Importar requests condicionalmente
try:
    # requests ya importado
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from pex.adapters import LLMAdapter, DBAdapter


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tool Adapter
# ─────────────────────────────────────────────────────────────────────────────

class MCPToolAdapter:
    """
    Adapter para herramientas MCP externas.
    
    Permite invocar tools expuestas por servidores MCP.
    """
    
    def __init__(self, server_url: str, server_name: str = "mcp"):
        """
        Inicializa el adapter MCP.
        
        Args:
            server_url: URL del servidor MCP (ej: http://localhost:8080)
            server_name: Nombre identificador del servidor
        """
        self.server_url = server_url.rstrip('/')
        self.server_name = server_name
        self.is_configured = False
        self.available_tools: List[Dict] = []
        self._last_connection_check = 0
        
        # Intentar conexión inicial
        self._check_connection()
    
    def _check_connection(self):
        """Verifica conexión con el servidor MCP."""
        try:
            # requests ya importado
            
            # Listar tools disponibles
            response = requests.get(
                f"{self.server_url}/tools",
                timeout=5
            )
            
            if response.status_code == 200:
                self.available_tools = response.json().get("tools", [])
                self.is_configured = True
                self._last_connection_check = time.time()
            else:
                self.is_configured = False
                
        except ImportError:
            self.is_configured = False
        except Exception:
            self.is_configured = False
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Invoca una tool del servidor MCP.
        
        Args:
            tool_name: Nombre de la tool a invocar
            arguments: Argumentos para la tool
        
        Returns:
            Resultado de la ejecución
        """
        if not self.is_configured:
            return {"error": "MCP server not connected", "tool": tool_name}
        
        # Verificar conexión periódicamente
        if time.time() - self._last_connection_check > 60:
            self._check_connection()
        
        try:
            # requests ya importado
            
            response = requests.post(
                f"{self.server_url}/tools/{tool_name}/invoke",
                json={"arguments": arguments},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"MCP error: {response.status_code}", "details": response.text}
                
        except Exception as e:
            return {"error": f"MCP call failed: {str(e)}"}
    
    def list_tools(self) -> List[Dict]:
        """Retorna lista de tools disponibles."""
        return self.available_tools.copy()
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """Obtiene el schema de una tool específica."""
        for tool in self.available_tools:
            if tool.get("name") == tool_name:
                return tool
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MCP Resource Adapter
# ─────────────────────────────────────────────────────────────────────────────

class MCPResourceAdapter:
    """
    Adapter para recursos MCP (datos, documentos, etc.).
    
    Permite leer recursos expuestos por servidores MCP.
    """
    
    def __init__(self, server_url: str, server_name: str = "mcp"):
        """
        Inicializa el adapter de recursos.
        
        Args:
            server_url: URL del servidor MCP
            server_name: Nombre identificador del servidor
        """
        self.server_url = server_url.rstrip('/')
        self.server_name = server_name
        self.is_configured = False
        self.available_resources: List[Dict] = []
        
        self._check_connection()
    
    def _check_connection(self):
        """Verifica conexión con el servidor MCP."""
        try:
            # requests ya importado
            
            response = requests.get(
                f"{self.server_url}/resources",
                timeout=5
            )
            
            if response.status_code == 200:
                self.available_resources = response.json().get("resources", [])
                self.is_configured = True
            else:
                self.is_configured = False
                
        except ImportError:
            self.is_configured = False
        except Exception:
            self.is_configured = False
    
    def read_resource(self, uri: str) -> Any:
        """
        Lee un recurso por URI.
        
        Args:
            uri: URI del recurso (ej: file:///path/to/doc.md)
        
        Returns:
            Contenido del recurso
        """
        if not self.is_configured:
            return {"error": "MCP server not connected"}
        
        try:
            # requests ya importado
            import urllib.parse
            
            # Codificar URI para URL
            encoded_uri = urllib.parse.quote(uri, safe='')
            
            response = requests.get(
                f"{self.server_url}/resources/{encoded_uri}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"MCP error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"MCP read failed: {str(e)}"}
    
    def list_resources(self) -> List[Dict]:
        """Retorna lista de recursos disponibles."""
        return self.available_resources.copy()


# ─────────────────────────────────────────────────────────────────────────────
# MCP Prompt Adapter
# ─────────────────────────────────────────────────────────────────────────────

class MCPPromptAdapter:
    """
    Adapter para prompts MCP.
    
    Permite ejecutar prompts predefinidos en servidores MCP.
    """
    
    def __init__(self, server_url: str, server_name: str = "mcp"):
        self.server_url = server_url.rstrip('/')
        self.server_name = server_name
        self.is_configured = False
        self.available_prompts: List[Dict] = []
        
        self._check_connection()
    
    def _check_connection(self):
        """Verifica conexión con el servidor MCP."""
        try:
            # requests ya importado
            
            response = requests.get(
                f"{self.server_url}/prompts",
                timeout=5
            )
            
            if response.status_code == 200:
                self.available_prompts = response.json().get("prompts", [])
                self.is_configured = True
            else:
                self.is_configured = False
                
        except ImportError:
            self.is_configured = False
        except Exception:
            self.is_configured = False
    
    def run_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Ejecuta un prompt predefinido.
        
        Args:
            prompt_name: Nombre del prompt
            arguments: Argumentos para el prompt
        
        Returns:
            Resultado del prompt
        """
        if not self.is_configured:
            return {"error": "MCP server not connected"}
        
        try:
            # requests ya importado
            
            response = requests.post(
                f"{self.server_url}/prompts/{prompt_name}/run",
                json={"arguments": arguments},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"MCP error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"MCP prompt failed: {str(e)}"}
    
    def list_prompts(self) -> List[Dict]:
        """Retorna lista de prompts disponibles."""
        return self.available_prompts.copy()


# ─────────────────────────────────────────────────────────────────────────────
# Factory Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_mcp_tool_adapter(server_url: str, server_name: str = "mcp") -> MCPToolAdapter:
    """
    Crea un adapter de tool MCP.
    
    Args:
        server_url: URL del servidor MCP
        server_name: Nombre del servidor
    
    Returns:
        Instancia de MCPToolAdapter
    """
    return MCPToolAdapter(server_url, server_name)


def get_mcp_resource_adapter(server_url: str, server_name: str = "mcp") -> MCPResourceAdapter:
    """
    Crea un adapter de recurso MCP.
    
    Args:
        server_url: URL del servidor MCP
        server_name: Nombre del servidor
    
    Returns:
        Instancia de MCPResourceAdapter
    """
    return MCPResourceAdapter(server_url, server_name)


def get_mcp_prompt_adapter(server_url: str, server_name: str = "mcp") -> MCPPromptAdapter:
    """
    Crea un adapter de prompt MCP.
    
    Args:
        server_url: URL del servidor MCP
        server_name: Nombre del servidor
    
    Returns:
        Instancia de MCPPromptAdapter
    """
    return MCPPromptAdapter(server_url, server_name)


# ─────────────────────────────────────────────────────────────────────────────
# MCP LLM Adapter (para servidores MCP que exponen modelos)
# ─────────────────────────────────────────────────────────────────────────────

class MCPLLMAdapter(LLMAdapter):
    """
    Adapter LLM que usa servidores MCP como backend.
    
    Útil para usar modelos locales o personalizados vía MCP.
    """
    
    def __init__(self, server_url: str, model_name: str = "default", **kwargs):
        super().__init__(model_name)
        self.server_url = server_url.rstrip('/')
        self.is_configured = False
        
        self._check_connection()
    
    def _check_connection(self):
        """Verifica conexión con el servidor MCP."""
        try:
            # requests ya importado
            
            response = requests.get(
                f"{self.server_url}/models",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                # Verificar si el modelo está disponible
                for model in models:
                    if model.get("name") == self.model_name or model.get("id") == self.model_name:
                        self.is_configured = True
                        break
        except ImportError:
            self.is_configured = False
        except Exception:
            self.is_configured = False
    
    def execute_intent(self, goal: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Ejecuta una intención usando el modelo MCP.
        
        Args:
            goal: Objetivo a cumplir
            inputs: Datos de entrada
            context: Contexto adicional
        
        Returns:
            Respuesta del modelo
        """
        if not self.is_configured:
            return f"[MCP Simulado] Goal: {goal}\n(Servidor MCP no conectado: {self.server_url})"
        
        try:
            # requests ya importado
            
            # Construir prompt desde goal + inputs + context
            prompt = self._build_prompt(goal, inputs, context)
            
            response = requests.post(
                f"{self.server_url}/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                return f"[MCP Error] {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"[MCP Error] {str(e)}"
    
    def _build_prompt(self, goal: str, inputs: Dict, context: Dict) -> str:
        """Construye prompt desde goal, inputs y contexto."""
        prompt = f"Objective: {goal}\n"
        
        if context:
            prompt += "\n--- Context ---\n"
            for k, v in context.items():
                prompt += f"{k}: {v}\n"
        
        if inputs:
            prompt += "\n--- Input Data ---\n"
            for k, v in inputs.items():
                if isinstance(v, (dict, list)):
                    import json
                    prompt += f"{k}: {json.dumps(v, indent=2)}\n"
                else:
                    prompt += f"{k}: {v}\n"
        
        prompt += "\nProvide a clear, concise response to fulfill the objective."
        return prompt
