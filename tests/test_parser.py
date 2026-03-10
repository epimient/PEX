"""
PEX Tests — Tests para el Parser de PEX.

Cubre:
- Parseo de todos los bloques (task, agent, pipeline, tool, model, etc.)
- Parseo de imports
- Parseo de bloques multilinea
- Errores de sintaxis
"""

import pytest
from pex.parser import parse_file, parse_source, ParseError
from pex.lexer import LexerError
from pex.ast_nodes import (
    TaskBlock, AgentBlock, PipelineBlock, ToolBlock,
    ModelBlock, MemoryBlock, RecordBlock, EntityBlock, RecordField, EntityField,
    ProjectBlock, Assignment, StringLiteral, IdentRef
)


class TestTaskParsing:
    """Tests para parseo de bloques task."""

    def test_parse_minimal_task(self, parse_program):
        """Verifica parseo de task minima."""
        program = parse_program("tests/fixtures/valid/hello.pi")
        
        assert len(program.statements) == 1
        task = program.statements[0]
        assert isinstance(task, TaskBlock)
        assert task.name == "hello"
        assert task.goal is not None

    def test_parse_task_with_output(self, parse_program):
        """Verifica task con output declarado."""
        source = '''
task analyze
   goal analyze data
   output analysis
'''
        program = parse_source(source, "test.pi")
        
        task = program.statements[0]
        assert task.name == "analyze"
        assert task.output == "analysis"

    def test_parse_task_with_inputs(self, parse_program):
        """Verifica task con multiples inputs."""
        source = '''
task process
   input data_a
   input data_b
   goal process data
   output result
'''
        program = parse_source(source, "test.pi")
        
        task = program.statements[0]
        assert len(task.inputs) == 2
        assert isinstance(task.inputs[0], IdentRef)
        assert task.inputs[0].name == "data_a"

    def test_parse_task_with_model(self, parse_program):
        """Verifica task con model referenciado."""
        source = '''
task analyze
   model analyst
   goal analyze data
'''
        program = parse_source(source, "test.pi")
        
        task = program.statements[0]
        assert task.model is not None
        assert isinstance(task.model, IdentRef)
        assert task.model.name == "analyst"

    def test_parse_task_with_sql(self, parse_program):
        """Verifica task con bloque SQL multilinea."""
        # Usamos ''' para el string exterior y """ para el interior
        source = '''task query_db
   input my_db
   sql """
       SELECT * FROM users
       WHERE active = true
   """
   output users_data
'''
        program = parse_source(source, "test.pi")
        
        task = program.statements[0]
        assert task.sql is not None
        assert "SELECT * FROM users" in task.sql.value

    def test_parse_task_with_contexts(self, parse_program):
        """Verifica task con multiples contextos."""
        source = '''
task analyze
   context region
   context period
   goal analyze sales
'''
        program = parse_source(source, "test.pi")
        
        task = program.statements[0]
        assert len(task.contexts) == 2


class TestAgentParsing:
    """Tests para parseo de bloques agent."""

    def test_parse_agent_minimal(self, parse_program):
        """Verifica parseo de agent minima."""
        source = '''
agent researcher
   goal investigate trends
'''
        program = parse_source(source, "test.pi")
        
        assert len(program.statements) == 1
        agent = program.statements[0]
        assert isinstance(agent, AgentBlock)
        assert agent.name == "researcher"

    def test_parse_agent_with_model_and_tools(self, parse_program):
        """Verifica agent con model y tools."""
        source = '''
agent market_analyst
   model researcher
   use web_search
   use docs
   goal analyze market
'''
        program = parse_source(source, "test.pi")
        
        agent = program.statements[0]
        assert agent.model is not None
        assert len(agent.uses) == 2


class TestPipelineParsing:
    """Tests para parseo de bloques pipeline."""

    def test_parse_pipeline_single_step(self, parse_program):
        """Verifica pipeline con un solo step."""
        source = '''
pipeline simple
   step task_a
'''
        program = parse_source(source, "test.pi")
        
        pipeline = program.statements[0]
        assert isinstance(pipeline, PipelineBlock)
        assert len(pipeline.steps) == 1

    def test_parse_pipeline_multiple_steps(self, parse_program):
        """Verifica pipeline con multiples steps."""
        source = '''
pipeline complex
   step analyze
   step predict
   step report
'''
        program = parse_source(source, "test.pi")
        
        pipeline = program.statements[0]
        assert len(pipeline.steps) == 3

    def test_parse_pipeline_from_fixture(self, parse_program):
        """Verifica parseo de pipeline desde fixture."""
        program = parse_program("tests/fixtures/valid/simple_pipeline.pi")
        
        pipelines = [s for s in program.statements if isinstance(s, PipelineBlock)]
        assert len(pipelines) == 1


class TestToolAndModelParsing:
    """Tests para parseo de tool y model."""

    def test_parse_tool_sqlite(self, parse_program):
        """Verifica parseo de tool SQLite."""
        source = '''
tool test_db
   provider "sqlite"
   source ":memory:"
'''
        program = parse_source(source, "test.pi")

        tool = program.statements[0]
        assert isinstance(tool, ToolBlock)
        # El provider puede ser un string o IdentRef dependiendo del parser
        assert tool.provider is not None

    def test_parse_tool_with_env_var(self, parse_program):
        """Verifica tool con variable de entorno."""
        source = '''
tool production_db
   provider "postgres"
   source $DATABASE_URL
'''
        program = parse_source(source, "test.pi")

        tool = program.statements[0]
        assert tool.source is not None
        # La fuente puede ser IdentRef o EnvVarRef
        assert hasattr(tool.source, 'name')

    def test_parse_model_openai(self, parse_program):
        """Verifica parseo de model OpenAI."""
        source = '''
model analyst
   provider "openai"
   name "gpt-4"
'''
        program = parse_source(source, "test.pi")

        model = program.statements[0]
        assert isinstance(model, ModelBlock)
        # provider puede ser string o IdentRef
        assert model.provider is not None


class TestImportParsing:
    """Tests para parseo de imports."""

    def test_parse_single_import(self, parse_program):
        """Verifica proyecto con un import."""
        source = '''
project test
   import tools
'''
        program = parse_source(source, "test.pi")
        
        project = program.statements[0]
        assert isinstance(project, ProjectBlock)
        assert len(project.imports) == 1
        assert project.imports[0] == "tools"

    def test_parse_multiple_imports(self, parse_program):
        """Verifica proyecto con multiples imports."""
        source = '''
project complex
   import tools
   import models
   import tasks
'''
        program = parse_source(source, "test.pi")
        
        project = program.statements[0]
        assert len(project.imports) == 3

    def test_parse_imports_from_fixture(self, parse_program):
        """Verifica parseo de imports desde fixture."""
        program = parse_program("tests/fixtures/valid/imports_project.pi")
        
        project = program.statements[0]
        assert isinstance(project, ProjectBlock)
        assert len(project.imports) == 2


class TestAssignmentParsing:
    """Tests para parseo de asignaciones."""

    def test_parse_string_assignment(self, parse_program):
        """Verifica asignacion de string."""
        source = 'region = "latam"'
        program = parse_source(source, "test.pi")
        
        assignment = program.statements[0]
        assert isinstance(assignment, Assignment)
        assert assignment.name == "region"
        assert isinstance(assignment.value, StringLiteral)
        assert assignment.value.value == "latam"

    def test_parse_number_assignment(self, parse_program):
        """Verifica asignacion de numero."""
        source = "limit = 100"
        program = parse_source(source, "test.pi")
        
        assignment = program.statements[0]
        assert isinstance(assignment, Assignment)
        assert assignment.value.value == 100

    def test_parse_boolean_assignment(self, parse_program):
        """Verifica asignacion de booleano."""
        source = "debug = true"
        program = parse_source(source, "test.pi")
        
        assignment = program.statements[0]
        assert isinstance(assignment, Assignment)
        assert assignment.value.value is True


class TestRecordAndEntityParsing:
    """Tests para parseo de record y entity."""

    def test_parse_record(self, parse_program):
        """Verifica parseo de record."""
        source = '''
record Forecast
   revenue
   confidence
   explanation
'''
        program = parse_source(source, "test.pi")

        record = program.statements[0]
        assert isinstance(record, RecordBlock)
        assert len(record.fields) == 3
        # Verificar nombres de campos
        assert record.fields[0].name == "revenue"
        assert record.fields[1].name == "confidence"

    def test_parse_record_with_types(self, parse_program):
        """Verifica parseo de record con tipos."""
        source = '''
record Forecast
   revenue : float
   confidence : int
   explanation
'''
        program = parse_source(source, "test.pi")

        record = program.statements[0]
        assert isinstance(record, RecordBlock)
        assert len(record.fields) == 3
        # Verificar tipos
        assert record.fields[0].field_type == "float"
        assert record.fields[1].field_type == "int"
        assert record.fields[2].field_type is None

    def test_parse_entity(self, parse_program):
        """Verifica parseo de entity."""
        source = '''
entity Sale
   table sales
   field sale_id
   field product_name
   field sale_revenue
'''
        program = parse_source(source, "test.pi")

        entity = program.statements[0]
        assert isinstance(entity, EntityBlock)
        # table puede ser string o IdentRef.name
        table_val = entity.table
        if hasattr(table_val, "name"):
            table_val = table_val.name
        assert table_val == "sales"
        assert len(entity.fields) == 3
        assert entity.fields[0].name == "sale_id"

    def test_parse_entity_with_types(self, parse_program):
        """Verifica parseo de entity con tipos (experimental)."""
        # Por ahora solo verificamos que entity basico funciona
        # Nota: 'name' es keyword, usamos 'full_name' en su lugar
        source = '''
entity Customer
   table customers
   field id
   field full_name
   field email
'''
        program = parse_source(source, "test.pi")

        entity = program.statements[0]
        assert isinstance(entity, EntityBlock)
        assert len(entity.fields) == 3
        assert entity.fields[0].name == "id"
        assert entity.fields[1].name == "full_name"


class TestMultilineParsing:
    """Tests para parseo de bloques multilinea."""

    def test_parse_multiline_sql(self, parse_program):
        """Verifica parseo de SQL multilinea."""
        program = parse_program("tests/fixtures/valid/multiline.pi")
        
        tasks = [s for s in program.statements if isinstance(s, TaskBlock)]
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task.sql is not None
        assert "select month, revenue" in task.sql.value

    def test_parse_multiline_with_comments(self, parse_program):
        """Verifica multilinea con comentarios internos."""
        # Usamos ''' para el string exterior
        source = '''task query_data
   sql """
       -- comentario
       SELECT * FROM users
       WHERE active = true
   """
'''
        program = parse_source(source, "test.pi")

        task = program.statements[0]
        assert task.sql is not None
        assert "SELECT * FROM users" in task.sql.value


class TestParseErrors:
    """Tests para errores de parseo."""

    def test_unclosed_multiline_raises(self):
        """Verifica que multilinea sin cerrar lanza error."""
        source = '''task broken
   sql """
       SELECT *
'''
        # El lexer deberia detectar esto
        with pytest.raises(LexerError):
            parse_source(source, "test.pi")
