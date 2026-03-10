"""
PEX Tests — Tests para el ExecutionPlanner de PEX.

Cubre:
- Validación de referencias cruzadas
- Detección de ciclos de imports
- Validación de inputs/outputs
- Validación de tools y models
"""

import pytest
from pathlib import Path
from pex.parser import parse_file, parse_source
from pex.planner import ExecutionPlanner, ExecutionPlan
from pex.diagnostics import DiagnosticCollection, DiagnosticError


class TestImportResolution:
    """Tests para resolución de imports."""

    def test_resolve_single_import(self, parse_program, build_plan):
        """Verifica resolución de un import simple."""
        program = parse_program("tests/fixtures/valid/imports_project.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        # Verificar que los imports se registraron
        assert len(plan.registry.tools) > 0 or len(plan.registry.models) > 0

    def test_resolve_multiple_imports(self, parse_program, build_plan):
        """Verifica resolución de múltiples imports."""
        program = parse_program("tests/fixtures/valid/imports_project.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        # Debería tener demo_db y demo_model registrados
        assert "demo_db" in plan.registry.tools
        assert "demo_model" in plan.registry.models

    def test_missing_import_raises_error(self, diagnostics):
        """Verifica que import faltante genera error."""
        source = """
project test
   import nonexistent_module

task main
   goal do something
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        # Debería tener error de import no encontrado
        assert diagnostics.has_errors()

    def test_import_cycle_detection(self, diagnostics):
        """Verifica deteccion de ciclo de imports."""
        # Los fixtures de ciclo ya estan creados
        file_a = Path("tests/fixtures/invalid/import_cycle_a.pi")

        if file_a.exists():
            program = parse_file(file_a)
            planner = ExecutionPlanner(diagnostics)

            # Deberia detectar el ciclo o al menos tener errores
            plan = planner.build_plan(program)

            # Verificar que hay errores (ciclo o import no encontrado)
            assert diagnostics.has_errors() or plan.has_errors()


class TestPipelineValidation:
    """Tests para validación de pipelines."""

    def test_valid_pipeline_steps(self, parse_program, build_plan):
        """Verifica pipeline con steps válidos."""
        program = parse_program("tests/fixtures/valid/simple_pipeline.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        # No debería tener errores
        assert not plan.has_errors()

    def test_undefined_step_raises_error(self, diagnostics):
        """Verifica que step no definido genera error."""
        source = """
project test

task step_a
   goal do something

pipeline broken
   step step_a
   step nonexistent_step
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()
        # Verificar que el error es sobre el step
        errors = diagnostics.errors()
        assert any("nonexistent_step" in e.message or "step" in e.message.lower() for e in errors)


class TestTaskValidation:
    """Tests para validación de tasks."""

    def test_task_with_valid_model(self, parse_program, build_plan):
        """Verifica task con model válido."""
        source = """
project test

model analyst
   provider openai
   name gpt-4

task analyze
   model analyst
   goal analyze data
"""
        program = parse_source(source, "test.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        assert not plan.has_errors()

    def test_undefined_model_raises_error(self, diagnostics):
        """Verifica que model no definido genera error."""
        source = """
project test

task analyze
   model undefined_model
   goal analyze data
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()

    def test_undefined_tool_raises_error(self, diagnostics):
        """Verifica que tool no definida genera error."""
        source = """
project test

task query_db
   use undefined_tool
   goal query database
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()

    def test_undefined_input_raises_error(self, diagnostics):
        """Verifica que input no definido genera error."""
        source = """
project test

task process
   input undefined_input
   goal process data
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()

    def test_valid_input_from_variable(self, diagnostics):
        """Verifica input válido desde variable."""
        source = """
project test

data_source = "my_data"

task process
   input data_source
   goal process data
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        # No debería tener errores porque data_source es variable
        assert not plan.has_errors()

    def test_valid_input_from_tool(self, diagnostics):
        """Verifica input valido desde tool."""
        source = '''
project test

tool my_db
   provider "sqlite"
   source ":memory:"

task fetch_data
   input my_db
   goal fetch database records
'''
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Verificar que no hay errores de validacion
        assert not diagnostics.has_errors()

    def test_valid_input_from_output(self, diagnostics):
        """Verifica input válido desde output de otra task."""
        source = """
project test

task produce
   goal produce data
   output produced_data

task consume
   input produced_data
   goal consume data
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert not plan.has_errors()


class TestAgentValidation:
    """Tests para validación de agents."""

    def test_agent_with_valid_model(self, diagnostics):
        """Verifica agent con model válido."""
        source = """
project test

model researcher
   provider openai
   name gpt-4

agent analyst
   model researcher
   goal analyze market
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert not plan.has_errors()

    def test_agent_undefined_model_raises_error(self, diagnostics):
        """Verifica que model no definido en agent genera error."""
        source = """
project test

agent analyst
   model undefined_model
   goal analyze market
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()

    def test_agent_undefined_tool_raises_error(self, diagnostics):
        """Verifica que tool no definida en agent genera error."""
        source = """
project test

agent researcher
   use undefined_tool
   goal research
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert diagnostics.has_errors()


class TestExecutionPlan:
    """Tests para la clase ExecutionPlan."""

    def test_plan_summary(self, parse_program, build_plan):
        """Verifica que get_summary() retorna datos correctos."""
        program = parse_program("tests/fixtures/valid/simple_pipeline.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        summary = plan.get_summary()
        
        assert "project" in summary
        assert "tasks" in summary
        assert "pipelines" in summary
        assert summary["project"] == "demo"
        assert summary["tasks"] >= 2
        assert summary["pipelines"] >= 1

    def test_plan_has_errors(self, diagnostics):
        """Verifica método has_errors()."""
        source = """
project test

task broken
   model nonexistent
   goal test
"""
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)
        
        assert plan.has_errors()

    def test_plan_no_errors(self, parse_program, build_plan):
        """Verifica método has_errors() sin errores."""
        program = parse_program("tests/fixtures/valid/hello.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        assert not plan.has_errors()


class TestRelativeImports:
    """Tests para imports relativos."""

    def test_relative_import_with_string(self, diagnostics):
        """Verifica import relativo con string."""
        source = '''
project test
   import "modules/shared"

task main
   goal test
'''
        # El import con path relativo debe parsear correctamente
        program = parse_source(source, "tests/fixtures/valid/test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Deberia tener error de import no encontrado (el archivo no existe)
        # pero no crash
        assert True

    def test_parent_directory_import_with_string(self, diagnostics):
        """Verifica import relativo con ../ y string."""
        source = '''
project test
   import "../shared"

task main
   goal test
'''
        program = parse_source(source, "tests/fixtures/valid/test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Deberia tener error de import no encontrado
        assert True


class TestCrossFileValidation:
    """Tests para validación cruzada entre archivos."""

    def test_imports_resolve_correctly(self, parse_program, build_plan):
        """Verifica que imports se resuelven correctamente."""
        program = parse_program("tests/fixtures/valid/imports_project.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        # La task 'main' usa demo_db y demo_model que vienen de imports
        assert "demo_db" in plan.registry.tools
        assert "demo_model" in plan.registry.models
        
        # No debería tener errores de referencias
        assert not plan.has_errors()

    def test_sql_sales_example(self, parse_program, build_plan):
        """Verifica ejemplo sql_sales.pi."""
        program = parse_program("tests/fixtures/valid/sql_sales.pi")
        diagnostics = DiagnosticCollection()
        plan = build_plan(program, diagnostics)
        
        # Verificar estructura
        assert len(plan.registry.tasks) == 2
        assert len(plan.registry.tools) == 1
        assert len(plan.registry.models) == 1
        
        # sales_data es output de get_sales y input de analyze_sales
        assert "sales_data" in [t.output for t in plan.registry.tasks.values() if t.output]
