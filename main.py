#!/usr/bin/env python3
"""
PEX — Punto de entrada principal del intérprete.
Uso:
    python main.py run <archivo.pi>
    python main.py check <archivo.pi>
    python main.py version
"""

from pex.cli import main

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if __name__ == "__main__":
    main()
