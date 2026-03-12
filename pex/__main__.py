#!/usr/bin/env python3
"""
PEX — Punto de entrada para el comando `pex`.

Uso:
    pex run <archivo.pi>     Ejecutar un programa PEX
    pex check <archivo.pi>   Verificar sintaxis sin ejecutar
    pex ast <archivo.pi>     Mostrar el AST
    pex plan <archivo.pi>    Mostrar plan de ejecución
    pex lint <archivo.pi>    Analizar código estáticamente
    pex version              Mostrar versión
"""

from pex.cli import main

if __name__ == "__main__":
    main()
