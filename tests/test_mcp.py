"""
PEX Tests — Tests para MCP Adapters.

Nota: Los tests que requieren conexión real se saltan si no hay requests instalado.
"""

import pytest
from pex.adapters.mcp import (
    MCPToolAdapter,
    MCPResourceAdapter,
    MCPPromptAdapter,
    MCPLLMAdapter,
    get_mcp_tool_adapter,
    get_mcp_resource_adapter,
    get_mcp_prompt_adapter,
    REQUESTS_AVAILABLE,
)


class TestMCPToolAdapter:
    """Tests para MCP Tool Adapter."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests no disponible")
    def test_mcp_tool_adapter_init_no_connection(self):
        """Verifica inicialización sin conexión."""
        adapter = MCPToolAdapter("http://nonexistent:9999", "test_server")

        # Debería intentar conectar y fallar
        assert adapter.is_configured is False
        assert len(adapter.available_tools) == 0

    def test_mcp_call_tool_not_configured(self):
        """Verifica llamada cuando adapter no está configurado."""
        adapter = MCPToolAdapter("http://localhost:8080", "test_server")
        adapter.is_configured = False

        result = adapter.call_tool("search", {"query": "test"})

        assert "error" in result
        assert "not connected" in result["error"]

    def test_mcp_list_tools(self):
        """Verifica listado de tools disponibles."""
        adapter = MCPToolAdapter("http://localhost:8080", "test_server")
        adapter.available_tools = [
            {"name": "search", "description": "Search web"},
            {"name": "analyze", "description": "Analyze data"}
        ]

        tools = adapter.list_tools()

        assert len(tools) == 2
        assert tools[0]["name"] == "search"

    def test_mcp_get_tool_schema(self):
        """Verifica obtención de schema de tool."""
        adapter = MCPToolAdapter("http://localhost:8080", "test_server")
        adapter.available_tools = [
            {"name": "search", "description": "Search web", "parameters": {"type": "object"}},
            {"name": "analyze", "description": "Analyze data"}
        ]

        schema = adapter.get_tool_schema("search")

        assert schema is not None
        assert schema["name"] == "search"
        assert schema["description"] == "Search web"

    def test_mcp_get_tool_schema_not_found(self):
        """Verifica schema de tool no encontrada."""
        adapter = MCPToolAdapter("http://localhost:8080", "test_server")
        adapter.available_tools = [{"name": "search"}]

        schema = adapter.get_tool_schema("nonexistent")

        assert schema is None


class TestMCPResourceAdapter:
    """Tests para MCP Resource Adapter."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests no disponible")
    def test_mcp_resource_adapter_init_no_connection(self):
        """Verifica inicialización sin conexión."""
        adapter = MCPResourceAdapter("http://nonexistent:9999", "test_server")

        assert adapter.is_configured is False

    def test_mcp_read_resource_not_configured(self):
        """Verifica lectura cuando adapter no está configurado."""
        adapter = MCPResourceAdapter("http://localhost:8080", "test_server")
        adapter.is_configured = False

        result = adapter.read_resource("file:///doc.md")

        assert "error" in result
        assert "not connected" in result["error"]

    def test_mcp_list_resources(self):
        """Verifica listado de recursos disponibles."""
        adapter = MCPResourceAdapter("http://localhost:8080", "test_server")
        adapter.available_resources = [
            {"uri": "file:///doc1.md", "name": "Doc 1"},
            {"uri": "file:///doc2.md", "name": "Doc 2"}
        ]

        resources = adapter.list_resources()

        assert len(resources) == 2
        assert resources[0]["uri"] == "file:///doc1.md"


class TestMCPPromptAdapter:
    """Tests para MCP Prompt Adapter."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests no disponible")
    def test_mcp_prompt_adapter_init_no_connection(self):
        """Verifica inicialización sin conexión."""
        adapter = MCPPromptAdapter("http://nonexistent:9999", "test_server")

        assert adapter.is_configured is False

    def test_mcp_run_prompt_not_configured(self):
        """Verifica ejecución cuando adapter no está configurado."""
        adapter = MCPPromptAdapter("http://localhost:8080", "test_server")
        adapter.is_configured = False

        result = adapter.run_prompt("summarize", {"text": "Long text here"})

        assert "error" in result
        assert "not connected" in result["error"]

    def test_mcp_list_prompts(self):
        """Verifica listado de prompts disponibles."""
        adapter = MCPPromptAdapter("http://localhost:8080", "test_server")
        adapter.available_prompts = [
            {"name": "summarize", "description": "Summarize text"},
            {"name": "expand", "description": "Expand ideas"}
        ]

        prompts = adapter.list_prompts()

        assert len(prompts) == 2
        assert prompts[0]["name"] == "summarize"


class TestMCPLLMAdapter:
    """Tests para MCP LLM Adapter."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests no disponible")
    def test_mcp_llm_adapter_init_no_connection(self):
        """Verifica inicialización sin conexión."""
        adapter = MCPLLMAdapter("http://nonexistent:9999", "llama3")

        assert adapter.is_configured is False

    def test_mcp_llm_execute_intent_not_configured(self):
        """Verifica ejecución cuando adapter no está configurado."""
        adapter = MCPLLMAdapter("http://localhost:8080", "llama3")
        adapter.is_configured = False

        result = adapter.execute_intent("Test goal", {}, {})

        assert "Simulado" in result or "simulado" in result.lower()

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests no disponible")
    def test_mcp_llm_build_prompt(self):
        """Verifica construcción de prompt."""
        adapter = MCPLLMAdapter("http://localhost:8080", "llama3")
        adapter.is_configured = False

        prompt = adapter._build_prompt(
            "Summarize this",
            {"text": "Long text here"},
            {"context": "business"}
        )

        assert "Summarize this" in prompt
        assert "Long text here" in prompt
        assert "context" in prompt.lower()


class TestMCPFactoryFunctions:
    """Tests para funciones factory de MCP."""

    def test_get_mcp_tool_adapter(self):
        """Verifica creación de tool adapter."""
        adapter = get_mcp_tool_adapter("http://localhost:8080", "test")

        assert isinstance(adapter, MCPToolAdapter)
        assert adapter.server_name == "test"

    def test_get_mcp_resource_adapter(self):
        """Verifica creación de resource adapter."""
        adapter = get_mcp_resource_adapter("http://localhost:8080", "test")

        assert isinstance(adapter, MCPResourceAdapter)
        assert adapter.server_name == "test"

    def test_get_mcp_prompt_adapter(self):
        """Verifica creación de prompt adapter."""
        adapter = get_mcp_prompt_adapter("http://localhost:8080", "test")

        assert isinstance(adapter, MCPPromptAdapter)
        assert adapter.server_name == "test"
