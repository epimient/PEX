"""
PEX Tests — Fixtures compartidos para todos los tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Retorna el directorio de fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures(fixtures_dir):
    """Retorna generator con todos los fixtures válidos."""
    return (fixtures_dir / "valid").glob("*.pi")


@pytest.fixture
def invalid_fixtures(fixtures_dir):
    """Retorna generator con todos los fixtures inválidos."""
    return (fixtures_dir / "invalid").glob("*.pi")


@pytest.fixture
def parse_program():
    """
    Fixture que provee función para parsear archivos.
    
    Uso:
        def test_something(parse_program):
            program = parse_program("path/to/file.pi")
    """
    from pex.parser import parse_file
    
    def _parse(path):
        return parse_file(path)
    
    return _parse


@pytest.fixture
def build_plan():
    """
    Fixture que provee función para construir planes.
    
    Uso:
        def test_something(build_plan):
            plan = build_plan(program)
    """
    from pex.planner import ExecutionPlanner
    from pex.diagnostics import DiagnosticCollection
    
    def _build(program, diagnostics=None):
        if diagnostics is None:
            diagnostics = DiagnosticCollection()
        planner = ExecutionPlanner(diagnostics)
        return planner.build_plan(program)
    
    return _build


@pytest.fixture
def diagnostics():
    """Fixture que provee una colección vacía de diagnósticos."""
    from pex.diagnostics import DiagnosticCollection
    return DiagnosticCollection()
