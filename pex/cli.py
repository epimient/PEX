"""
PEX CLI — Interfaz de línea de comandos para el intérprete PEX.

Comandos:
    pex run <archivo.pi>     Ejecutar un programa PEX
    pex check <archivo.pi>   Verificar sintaxis sin ejecutar
    pex version              Mostrar versión
"""

import sys
import os
from typing import List, Any
from pex import __version__
from pex.lexer import Lexer, LexerError
from pex.parser import Parser, ParseError, parse_file
from pex.planner import ExecutionPlanner, ExecutionPlan
from pex.diagnostics import DiagnosticError, DiagnosticCollection, DiagnosticKind
from pex.runtime import PexRuntime, Colors, _c
from pex.ast_utils import print_ast, ast_to_dict


def print_usage():
    print()
    print(_c(Colors.HEADER, "  PEX") + f" — Intérprete v{__version__}")
    print()
    print("  Uso:")
    print(f"    python main.py {_c(Colors.CYAN, 'ast')}     <archivo.pi>   [--json] [--full] Mostrar el AST")
    print(f"    python main.py {_c(Colors.MAGENTA, 'plan')}    <archivo.pi>   [--json] [--verbose] Ver plan")
    print(f"    python main.py {_c(Colors.GREEN, 'run')}     <archivo.pi>   [--dry-run] [--verbose] Ejecutar programa")
    print(f"    python main.py {_c(Colors.GREEN, 'check')}   <archivo.pi>   Verificar sintaxis sin ejecutar")
    print(f"    python main.py {_c(Colors.GREEN, 'lint')}    <archivo.pi>   [--verbose] Analizar código estáticamente")
    print(f"    python main.py {_c(Colors.GREEN, 'version')}               Mostrar versión")
    print()
    print("  Flags adicionales:")
    print("    --json      Salida en formato JSON para herramientas")
    print("    --full      En modo 'ast', muestra cadenas de texto completas")
    print("    --verbose   Muestra detalles extra de ejecución y warnings del linter")
    print("    --dry-run   Simula ejecución sin llamar adapters reales (LLM, DB)")
    print()


def _print_diagnostics(diagnostics: DiagnosticCollection, verbose: bool = False):
    """Imprime todos los diagnósticos acumulados."""
    if not diagnostics.diagnostics:
        return

    use_colors = True  # Podría hacerse configurable

    # Imprimir errores primero
    errors = diagnostics.errors()
    warnings = diagnostics.warnings()

    if errors:
        print()
        for diag in errors:
            print(diag.format(use_colors))

    if warnings and verbose:
        print()
        for diag in warnings:
            print(diag.format(use_colors))


def cmd_run(filepath: str, verbose: bool = True, dry_run: bool = False):
    """
    Ejecuta un archivo .pi

    Args:
        filepath: Ruta al archivo .pi
        verbose: Si True, muestra detalles de ejecución
        dry_run: Si True, simula ejecución sin llamar adapters reales
    """
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        diagnostics = DiagnosticCollection()
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Verificar si hay errores antes de ejecutar
        if plan.has_errors():
            _print_diagnostics(diagnostics, verbose=verbose)
            sys.exit(1)

        runtime = PexRuntime(verbose=verbose)

        if dry_run:
            # Modo dry-run: solo muestra el plan sin ejecutar
            print(_c(Colors.CYAN, "\n  ══ DRY-RUN MODE ══"))
            print(_c(Colors.DIM, "  (Simulación - sin llamadas a adapters reales)\n"))
            runtime.check_only(plan, filepath)
        else:
            runtime.execute(plan, filepath)

    except LexerError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except ParseError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except DiagnosticError as e:
        _print_diagnostics(e.collection, verbose=True)
        sys.exit(1)
    except Exception as e:
        print(_c(Colors.RED, f"\n  ✗ Error inesperado: {e}"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_check(filepath: str, verbose: bool = False):
    """Verifica la sintaxis de un archivo .pi sin ejecutar"""
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        diagnostics = DiagnosticCollection()
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Imprimir diagnósticos (errores y warnings si verbose)
        if plan.has_errors():
            _print_diagnostics(diagnostics, verbose=verbose)
            sys.exit(1)

        # Éxito - mostrar resumen
        runtime = PexRuntime(verbose=False)
        runtime.check_only(plan, filepath)

        # Mostrar warnings si los hay
        if verbose and diagnostics.has_warnings():
            _print_diagnostics(diagnostics, verbose=True)

    except LexerError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except ParseError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except DiagnosticError as e:
        _print_diagnostics(e.collection, verbose=True)
        sys.exit(1)


def cmd_lint(filepath: str, verbose: bool = False):
    """
    Analiza estáticamente un archivo .pi

    Args:
        filepath: Ruta al archivo .pi
        verbose: Si True, muestra warnings e info también
    """
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        from pex.linter import Linter, lint_program, LintLevel

        # Parsear y construir plan
        program = parse_file(filepath)
        diagnostics = DiagnosticCollection()
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Ejecutar linter
        linter = lint_program(program, plan.registry)
        results = linter.messages

        # Filtrar por nivel si no es verbose
        if not verbose:
            results = [m for m in results if m.level in (LintLevel.ERROR, LintLevel.WARNING)]

        # Mostrar resultados
        if results:
            print()
            print(_c(Colors.HEADER, "  ══ PEX Linter Results ══"))
            print()

            for msg in results:
                print(msg.format(use_colors=True))

            # Resumen
            summary = linter.summary()
            print()
            print(_c(Colors.DIM, f"  {summary['errors']} errors, {summary['warnings']} warnings, {summary['info']} info, {summary['hints']} hints"))

            # Exit code según errores
            if summary['errors'] > 0:
                sys.exit(1)
        else:
            print()
            print(_c(Colors.SUCCESS, "  ✓ No issues found"))

    except LexerError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except ParseError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except DiagnosticError as e:
        _print_diagnostics(e.collection, verbose=True)
        sys.exit(1)
    except Exception as e:
        print(_c(Colors.RED, f"\n  ✗ Error en linter: {e}"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_ast(filepath: str, flags: List[str]):
    """Muestra el AST del archivo"""
    as_json = "--json" in flags
    full = "--full" in flags
    
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        if as_json:
            import json
            print(json.dumps(ast_to_dict(program), indent=2, ensure_ascii=False))
        else:
            print(f"\n{_c(Colors.CYAN, 'PEX AST')}")
            print(f"Archivo: {filepath}")
            print_ast(program, full=full)
    except Exception as e:
        print(_c(Colors.RED, f"\n  ✗ Error al generar AST: {e}"))
        sys.exit(1)


def cmd_plan(filepath: str, flags: List[str]):
    """Muestra el plan de ejecución semántico."""
    as_json = "--json" in flags
    verbose = "--verbose" in flags
    summary_only = "--summary" in flags

    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        diagnostics = DiagnosticCollection()
        planner = ExecutionPlanner(diagnostics)
        plan = planner.build_plan(program)

        # Verificar errores
        if plan.has_errors():
            _print_diagnostics(diagnostics, verbose=verbose)
            sys.exit(1)

        stat = plan.get_summary()

        if as_json:
            import json
            # Construimos un dict balanceado para el plan
            out = {
                "summary": stat,
                "steps": _get_plan_steps_dict(plan.registry)
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return

        print(f"\n{_c(Colors.MAGENTA, 'PEX Execution Plan')}")
        print(f"Archivo: {filepath}")
        print(f"Proyecto: {_c(Colors.CYAN, stat['project'])}")

        print(f"\n{_c(Colors.DIM, 'Plan Summary')}")
        print(f"  - tasks: {stat['tasks']}")
        print(f"  - pipelines: {stat['pipelines']}")
        print(f"  - tools: {stat['tools']}")
        print(f"  - models: {stat['models']}")

        if summary_only:
            return

        # Listar ejecución (pipelines y sus pasos)
        for p_name, pipe in plan.registry.pipelines.items():
            print(f"\n{_c(Colors.MAGENTA, 'Pipeline')}: {_c(Colors.YELLOW, p_name)}")
            print(f"  {'─' * 40}")
            for i, step_ref in enumerate(pipe.steps, 1):
                s_name = step_ref.name
                print(f"  {_c(Colors.DIM, f'Step {i}')} — {_c(Colors.GREEN, s_name)}")

                # Buscar detalle
                if s_name in plan.registry.tasks:
                    _print_task_plan(plan.registry.tasks[s_name], indent=4, verbose=verbose)
                elif s_name in plan.registry.agents:
                    _print_agent_plan(plan.registry.agents[s_name], indent=4, verbose=verbose)

    except DiagnosticError as e:
        _print_diagnostics(e.collection, verbose=True)
        sys.exit(1)
    except Exception as e:
        print(_c(Colors.RED, f"\n  ✗ Error al generar Plan: {e}"))
        import traceback
        if verbose: traceback.print_exc()
        sys.exit(1)

def _get_plan_steps_dict(registry: Any) -> list:
    steps = []
    for p_name, pipe in registry.pipelines.items():
        p_steps = []
        for step_ref in pipe.steps:
            s_name = step_ref.name
            details = {"name": s_name}
            if s_name in registry.tasks:
                t = registry.tasks[s_name]
                details.update({
                    "kind": "task",
                    "inputs": [str(i) for i in t.inputs],
                    "output": t.output
                })
            elif s_name in registry.agents:
                a = registry.agents[s_name]
                details.update({
                    "kind": "agent",
                    "model": str(a.model)
                })
            p_steps.append(details)
        steps.append({"pipeline": p_name, "steps": p_steps})
    return steps

def _print_task_plan(task: Any, indent: int = 4, verbose: bool = False):
    pad = " " * indent
    print(f"{pad}kind: task")
    if task.inputs:
        print(f"{pad}input: {[getattr(i, 'name', getattr(i, 'value', str(i))) for i in task.inputs]}")
    
    actions = []
    if task.inputs: actions.append("resolve inputs")
    if task.uses: actions.append("use specialized tools")
    if task.sql: actions.append("execute sql")
    if task.query: actions.append("execute query")
    if task.goal: actions.append("solve goal via LLM")
    if task.output: actions.append(f"store output in '{task.output}'")
    
    print(f"{pad}actions:")
    for a in actions:
        print(f"{pad}  - {a}")

def _print_agent_plan(agent: Any, indent: int = 4, verbose: bool = False):
    pad = " " * indent
    print(f"{pad}kind: agent")
    if agent.model:
        m_name = agent.model.name if hasattr(agent.model, 'name') else str(agent.model)
        print(f"{pad}model: {m_name}")
    print(f"{pad}actions:")
    print(f"{pad}  - invoke agentic loop")
    if agent.goal: print(f"{pad}  - pursue goal: {getattr(agent.goal, 'value', str(agent.goal))[:50]}...")

def main():
    args = sys.argv[1:]

    if not args:
        print_usage()
        sys.exit(0)

    # Identificar comando y archivo
    command = args[0].lower()

    if command == "version" or command == "--version":
        print(f"  PEX v{__version__}")
        sys.exit(0)

    # El segundo argumento debería ser el archivo .pi
    if len(args) < 2:
        if command in ("run", "check", "ast", "plan", "lint"):
            print(_c(Colors.RED, f"  ✗ Se requiere un archivo .pi"))
            print(f"  Uso: python main.py {command} <archivo.pi>")
            sys.exit(1)
        else:
            print_usage()
            sys.exit(1)

    filepath = args[1]
    flags = [a.lower() for a in args[2:]]

    # Parsear flags
    dry_run = "--dry-run" in flags or "--dry_run" in flags
    verbose = "--verbose" in flags  # Por defecto verbose es False

    if command == "run":
        cmd_run(filepath, verbose=verbose, dry_run=dry_run)
    elif command == "check":
        cmd_check(filepath, verbose=verbose)
    elif command == "lint":
        cmd_lint(filepath, verbose=verbose)
    elif command == "ast":
        cmd_ast(filepath, flags)
    elif command == "plan":
        cmd_plan(filepath, flags)
    else:
        print(_c(Colors.RED, f"  ✗ Comando desconocido: {command}"))
        print_usage()
        sys.exit(1)
