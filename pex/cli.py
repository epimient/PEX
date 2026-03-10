"""
PEX CLI — Interfaz de línea de comandos para el intérprete PEX.

Comandos:
    pex run <archivo.pi>     Ejecutar un programa PEX
    pex check <archivo.pi>   Verificar sintaxis sin ejecutar
    pex version              Mostrar versión
"""

import sys
import os
from pex import __version__
from pex.lexer import Lexer, LexerError
from pex.parser import Parser, ParseError, parse_file
from pex.runtime import PexRuntime, Colors, _c


def print_usage():
    print()
    print(_c(Colors.HEADER, "  PEX") + f" — Intérprete v{__version__}")
    print()
    print("  Uso:")
    print(f"    python main.py {_c(Colors.GREEN, 'run')}   <archivo.pi>   Ejecutar programa PEX")
    print(f"    python main.py {_c(Colors.YELLOW, 'check')} <archivo.pi>   Verificar sintaxis")
    print(f"    python main.py {_c(Colors.CYAN, 'version')}               Mostrar versión")
    print()


def cmd_run(filepath: str, verbose: bool = True):
    """Ejecuta un archivo .pi"""
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        runtime = PexRuntime(verbose=verbose)
        runtime.execute(program)
    except LexerError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except ParseError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except Exception as e:
        print(_c(Colors.RED, f"\n  ✗ Error inesperado: {e}"))
        sys.exit(1)


def cmd_check(filepath: str):
    """Verifica la sintaxis de un archivo .pi sin ejecutar"""
    if not os.path.exists(filepath):
        print(_c(Colors.RED, f"  ✗ Archivo no encontrado: {filepath}"))
        sys.exit(1)

    try:
        program = parse_file(filepath)
        runtime = PexRuntime(verbose=False)
        runtime.check_only(program)
    except LexerError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)
    except ParseError as e:
        print(_c(Colors.RED, f"\n  ✗ {e}"))
        sys.exit(1)


def main():
    args = sys.argv[1:]

    if not args:
        print_usage()
        sys.exit(0)

    command = args[0].lower()

    if command == "version":
        print(f"  PEX v{__version__}")
        sys.exit(0)

    if command in ("run", "check"):
        if len(args) < 2:
            print(_c(Colors.RED, f"  ✗ Se requiere un archivo .pi"))
            print(f"  Uso: python main.py {command} <archivo.pi>")
            sys.exit(1)

        filepath = args[1]

        if command == "run":
            cmd_run(filepath)
        else:
            cmd_check(filepath)
    else:
        print(_c(Colors.RED, f"  ✗ Comando desconocido: {command}"))
        print_usage()
        sys.exit(1)
