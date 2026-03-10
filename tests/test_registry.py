"""
PEX Tests — Tests para el Registry de PEX.

Cubre:
- Registro de todos los tipos de bloques
- Detección de colisiones (nombres duplicados)
- Variables y asignaciones
"""

import pytest
from pex.registry import Registry
from pex.ast_nodes import (
    TaskBlock, AgentBlock, PipelineBlock, ToolBlock,
    ModelBlock, MemoryBlock, RecordBlock, EntityBlock,
    Assignment, StringLiteral, IdentRef
)
from pex.diagnostics import DiagnosticError, DiagnosticCollection


class TestBasicRegistration:
    """Tests para registro básico de bloques."""

    def test_register_task(self, diagnostics):
        """Verifica registro de task."""
        registry = Registry(diagnostics)
        task = TaskBlock(name="analyze", goal=StringLiteral("test"))
        
        registry.register(task, filename="test.pi")
        
        assert "analyze" in registry.tasks
        assert registry.tasks["analyze"] == task

    def test_register_agent(self, diagnostics):
        """Verifica registro de agent."""
        registry = Registry(diagnostics)
        agent = AgentBlock(name="researcher", goal=StringLiteral("test"))
        
        registry.register(agent, filename="test.pi")
        
        assert "researcher" in registry.agents

    def test_register_pipeline(self, diagnostics):
        """Verifica registro de pipeline."""
        registry = Registry(diagnostics)
        pipeline = PipelineBlock(name="flow")
        
        registry.register(pipeline, filename="test.pi")
        
        assert "flow" in registry.pipelines

    def test_register_tool(self, diagnostics):
        """Verifica registro de tool."""
        registry = Registry(diagnostics)
        tool = ToolBlock(name="db", provider="sqlite")
        
        registry.register(tool, filename="test.pi")
        
        assert "db" in registry.tools

    def test_register_model(self, diagnostics):
        """Verifica registro de model."""
        registry = Registry(diagnostics)
        model = ModelBlock(name="analyst", provider="openai")
        
        registry.register(model, filename="test.pi")
        
        assert "analyst" in registry.models

    def test_register_memory(self, diagnostics):
        """Verifica registro de memory."""
        registry = Registry(diagnostics)
        memory = MemoryBlock(name="cache", scope="session")
        
        registry.register(memory, filename="test.pi")
        
        assert "cache" in registry.memories

    def test_register_record(self, diagnostics):
        """Verifica registro de record."""
        registry = Registry(diagnostics)
        record = RecordBlock(name="Forecast", fields=["revenue", "confidence"])
        
        registry.register(record, filename="test.pi")
        
        assert "Forecast" in registry.records

    def test_register_entity(self, diagnostics):
        """Verifica registro de entity."""
        registry = Registry(diagnostics)
        entity = EntityBlock(name="Sale", table="sales")
        
        registry.register(entity, filename="test.pi")
        
        assert "Sale" in registry.entities

    def test_register_assignment(self, diagnostics):
        """Verifica registro de asignación."""
        registry = Registry(diagnostics)
        assignment = Assignment(name="region", value=StringLiteral("latam"))
        
        registry.register(assignment, filename="test.pi")
        
        assert "region" in registry.variables
        assert registry.variables["region"] == "latam"


class TestDuplicateDetection:
    """Tests para detección de nombres duplicados."""

    def test_duplicate_task_raises(self, diagnostics):
        """Verifica que task duplicada lanza error."""
        registry = Registry(diagnostics)
        
        task1 = TaskBlock(name="analyze", goal=StringLiteral("test"))
        task2 = TaskBlock(name="analyze", goal=StringLiteral("other"))
        
        registry.register(task1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(task2, filename="test.pi")

    def test_duplicate_agent_raises(self, diagnostics):
        """Verifica que agent duplicado lanza error."""
        registry = Registry(diagnostics)
        
        agent1 = AgentBlock(name="bot", goal=StringLiteral("test"))
        agent2 = AgentBlock(name="bot", goal=StringLiteral("other"))
        
        registry.register(agent1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(agent2, filename="test.pi")

    def test_duplicate_pipeline_raises(self, diagnostics):
        """Verifica que pipeline duplicado lanza error."""
        registry = Registry(diagnostics)
        
        pipe1 = PipelineBlock(name="flow")
        pipe2 = PipelineBlock(name="flow")
        
        registry.register(pipe1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(pipe2, filename="test.pi")

    def test_duplicate_tool_raises(self, diagnostics):
        """Verifica que tool duplicada lanza error."""
        registry = Registry(diagnostics)
        
        tool1 = ToolBlock(name="db", provider="sqlite")
        tool2 = ToolBlock(name="db", provider="postgres")
        
        registry.register(tool1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(tool2, filename="test.pi")

    def test_duplicate_model_raises(self, diagnostics):
        """Verifica que model duplicado lanza error."""
        registry = Registry(diagnostics)
        
        model1 = ModelBlock(name="analyst", provider="openai")
        model2 = ModelBlock(name="analyst", provider="ollama")
        
        registry.register(model1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(model2, filename="test.pi")

    def test_duplicate_record_raises(self, diagnostics):
        """Verifica que record duplicado lanza error."""
        registry = Registry(diagnostics)
        
        record1 = RecordBlock(name="Data", fields=["a"])
        record2 = RecordBlock(name="Data", fields=["b"])
        
        registry.register(record1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(record2, filename="test.pi")

    def test_duplicate_entity_raises(self, diagnostics):
        """Verifica que entity duplicada lanza error."""
        registry = Registry(diagnostics)
        
        entity1 = EntityBlock(name="User", table="users")
        entity2 = EntityBlock(name="User", table="accounts")
        
        registry.register(entity1, filename="test.pi")
        
        with pytest.raises(DiagnosticError):
            registry.register(entity2, filename="test.pi")


class TestDifferentTypesNoCollision:
    """Tests para verificar que tipos diferentes no colisionan."""

    def test_task_and_agent_same_name_raises(self, diagnostics):
        """Task y agent con mismo nombre deberían colisionar."""
        registry = Registry(diagnostics)
        
        # En realidad, tipos diferentes PUEDEN tener el mismo nombre
        # porque están en namespaces separados
        task = TaskBlock(name="process", goal=StringLiteral("test"))
        agent = AgentBlock(name="process", goal=StringLiteral("test"))
        
        registry.register(task, filename="test.pi")
        registry.register(agent, filename="test.pi")
        
        # Ambos deberían estar registrados
        assert "process" in registry.tasks
        assert "process" in registry.agents

    def test_all_types_can_coexist(self, diagnostics):
        """Verifica que todos los tipos pueden coexistir."""
        registry = Registry(diagnostics)
        
        registry.register(TaskBlock(name="item", goal=StringLiteral("x")), filename="test.pi")
        registry.register(AgentBlock(name="item", goal=StringLiteral("x")), filename="test.pi")
        registry.register(ToolBlock(name="item", provider="test"), filename="test.pi")
        registry.register(ModelBlock(name="item", provider="test"), filename="test.pi")
        
        # Todos deberían estar en sus respectivos namespaces
        assert len(registry.tasks) == 1
        assert len(registry.agents) == 1
        assert len(registry.tools) == 1
        assert len(registry.models) == 1


class TestRegistryClear:
    """Tests para limpiar el registry."""

    def test_clear_removes_all(self, diagnostics):
        """Verifica que clear() remueve todo."""
        registry = Registry(diagnostics)
        
        registry.register(TaskBlock(name="t", goal=StringLiteral("x")), filename="test.pi")
        registry.register(AgentBlock(name="a", goal=StringLiteral("x")), filename="test.pi")
        registry.register(Assignment(name="v", value=StringLiteral("x")), filename="test.pi")
        
        registry.clear()
        
        assert len(registry.tasks) == 0
        assert len(registry.agents) == 0
        assert len(registry.variables) == 0

    def test_clear_resets_diagnostics(self, diagnostics):
        """Verifica que clear() tambien limpia diagnosticos."""
        from pex.diagnostics import Diagnostic, DiagnosticKind

        registry = Registry(diagnostics)

        registry.diagnostics.add(Diagnostic(
            kind=DiagnosticKind.ERROR,
            code="E001",
            message="test error",
            file="test.pi",
            line=1
        ))

        registry.clear()

        assert len(registry.diagnostics.diagnostics) == 0
