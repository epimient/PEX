"""
PEX Tests — Tests para el Linter.
"""

import pytest
from pex.linter import (
    Linter,
    LintLevel,
    LintMessage,
    UnusedVariableRule,
    UnusedImportRule,
    TaskWithoutOutputRule,
    NamingConventionRule,
    EmptyBlockRule,
    lint_program,
)


class TestLinter:
    """Tests para el Linter principal."""

    def test_linter_no_issues(self, diagnostics):
        """Verifica linter sin problemas."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
task hello
   goal say hello to the world
'''
        program = parse_source(source, "hello.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        linter = lint_program(program, plan.registry)

        assert len(linter.messages) == 0 or all(
            m.level in (LintLevel.INFO, LintLevel.HINT)
            for m in linter.messages
        )

    def test_linter_summary(self, diagnostics):
        """Verifica resumen del linter."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
task hello
   goal say hello
'''
        program = parse_source(source, "hello.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        linter = lint_program(program, plan.registry)
        summary = linter.summary()

        assert "errors" in summary
        assert "warnings" in summary
        assert "info" in summary
        assert "hints" in summary

    def test_linter_has_errors(self):
        """Verifica detección de errores."""
        linter = Linter()
        linter.messages = [
            LintMessage(
                level=LintLevel.ERROR,
                code="E001",
                message="Test error",
                file="test.pi",
                line=1,
            )
        ]
        
        assert linter.has_errors() is True

    def test_linter_has_warnings(self):
        """Verifica detección de warnings."""
        linter = Linter()
        linter.messages = [
            LintMessage(
                level=LintLevel.WARNING,
                code="W001",
                message="Test warning",
                file="test.pi",
                line=1,
            )
        ]
        
        assert linter.has_warnings() is True

    def test_linter_format_results(self, diagnostics):
        """Verifica formateo de resultados."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
task hello
   goal say hello
'''
        program = parse_source(source, "hello.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        linter = lint_program(program, plan.registry)
        formatted = linter.format_results(use_colors=False)

        # Si hay mensajes, el formato debería ser string no vacío
        if linter.messages:
            assert isinstance(formatted, str)


class TestUnusedVariableRule:
    """Tests para regla de variables no usadas."""

    def test_unused_variable_detection(self, diagnostics):
        """Verifica detección de variables no usadas."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
project test
unused_var = "never_used"

task hello
   goal say hello
'''
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        rule = UnusedVariableRule()
        messages = rule.check(program, plan.registry)

        # Debería detectar unused_var
        assert len(messages) >= 1
        assert any("unused_var" in m.message for m in messages)


class TestTaskWithoutOutputRule:
    """Tests para regla de tasks sin output."""

    def test_task_without_output(self, diagnostics):
        """Verifica detección de task sin output."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
project test

model ai
   provider openai
   name gpt-4

task analyze
   model ai
   goal analyze data
'''
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        rule = TaskWithoutOutputRule()
        messages = rule.check(program, plan.registry)

        # Debería detectar task sin output
        assert len(messages) >= 1
        assert any("analyze" in m.message for m in messages)


class TestNamingConventionRule:
    """Tests para regla de convenciones de naming."""

    def test_snake_case_validation(self, diagnostics):
        """Verifica validación de snake_case."""
        rule = NamingConventionRule()

        assert rule._is_snake_case("my_task") is True
        assert rule._is_snake_case("task_name") is True
        assert rule._is_snake_case("MyTask") is False
        assert rule._is_snake_case("taskName") is False

    def test_pascal_case_validation(self, diagnostics):
        """Verifica validación de PascalCase."""
        rule = NamingConventionRule()

        assert rule._is_pascal_case("MyRecord") is True
        assert rule._is_pascal_case("Record") is True
        assert rule._is_pascal_case("my_record") is False
        assert rule._is_pascal_case("myRecord") is False

    def test_to_snake_case_conversion(self, diagnostics):
        """Verifica conversión a snake_case."""
        rule = NamingConventionRule()

        assert rule._to_snake_case("MyTask") == "my_task"
        assert rule._to_snake_case("TaskName") == "task_name"

    def test_to_pascal_case_conversion(self, diagnostics):
        """Verifica conversión a PascalCase."""
        rule = NamingConventionRule()

        assert rule._to_pascal_case("my_task") == "MyTask"
        assert rule._to_pascal_case("task_name") == "TaskName"


class TestEmptyBlockRule:
    """Tests para regla de bloques vacíos."""

    def test_task_without_goal(self, diagnostics):
        """Verifica detección de task sin goal."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
project test

task no_goal
   input data
   output result
'''
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        rule = EmptyBlockRule()
        messages = rule.check(program, plan.registry)

        # Debería detectar task sin goal
        assert len(messages) >= 1
        assert any("no_goal" in m.message for m in messages)

    def test_agent_without_goal(self, diagnostics):
        """Verifica detección de agent sin goal."""
        from pex.parser import parse_source
        from pex.planner import ExecutionPlanner

        source = '''
project test

agent no_goal_agent
   model ai
'''
        program = parse_source(source, "test.pi")
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        rule = EmptyBlockRule()
        messages = rule.check(program, plan.registry)

        # Debería detectar agent sin goal
        assert len(messages) >= 1
        assert any("no_goal_agent" in m.message for m in messages)


class TestLintMessage:
    """Tests para mensajes de lint."""

    def test_lint_message_format(self):
        """Verifica formateo de mensaje."""
        msg = LintMessage(
            level=LintLevel.WARNING,
            code="W001",
            message="Variable no usada",
            file="test.pi",
            line=10,
            column=5,
            suggestion="Eliminar variable",
        )
        
        formatted = msg.format(use_colors=False)
        
        assert "W001" in formatted
        assert "WARNING" in formatted
        assert "Variable no usada" in formatted
        assert "test.pi:10:5" in formatted
        assert "Eliminar variable" in formatted

    def test_lint_message_without_column(self):
        """Verifica mensaje sin columna."""
        msg = LintMessage(
            level=LintLevel.ERROR,
            code="E001",
            message="Error grave",
            file="test.pi",
            line=5,
        )
        
        formatted = msg.format(use_colors=False)
        
        assert "E001" in formatted
        assert "ERROR" in formatted
        assert "test.pi:5" in formatted


class TestLintLevel:
    """Tests para niveles de lint."""

    def test_lint_level_values(self):
        """Verifica valores de niveles."""
        assert LintLevel.ERROR.value == "error"
        assert LintLevel.WARNING.value == "warning"
        assert LintLevel.INFO.value == "info"
        assert LintLevel.HINT.value == "hint"
