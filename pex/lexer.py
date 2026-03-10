"""
PEX Lexer — Análisis léxico del lenguaje PEX.

Convierte código fuente .pi en una secuencia de tokens,
manejando indentación al estilo Python para definir bloques.
Soporta bloques multilínea con \"\"\".
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    # Estructuras
    KEYWORD = auto()
    IDENT = auto()

    # Literales
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    ENV_VAR = auto()

    # Operadores
    ASSIGN = auto()       # =

    # Control de estructura
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()

    # Texto libre (para goal, query, etc.)
    TEXT = auto()


# Palabras clave del lenguaje PEX v0.1
KEYWORDS = {
    # Bloques principales
    "project", "task", "agent", "pipeline", "tool", "model", "memory",
    # Sub-bloques / propiedades
    "import", "step", "input", "goal", "context", "output", "use",
    "provider", "name", "source", "scope", "sql", "query", "filter",
    # Estructuras de datos
    "record", "entity", "field", "table",
}

# Propiedades que aceptan texto libre hasta fin de línea o bloque multilínea
FREE_TEXT_PROPERTIES = {"goal", "query", "filter", "sql"}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        val = repr(self.value) if self.type != TokenType.NEWLINE else "\\n"
        return f"Token({self.type.name}, {val}, L{self.line})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Error léxico en línea {line}, columna {column}: {message}")


class Lexer:
    """Tokenizador para archivos .pi de PEX."""

    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack: List[int] = [0]  # pila de niveles de indentación

    def tokenize(self) -> List[Token]:
        """Genera la lista completa de tokens."""
        lines = self.source.split("\n")
        
        in_multiline = False
        multiline_lines = []
        multiline_start_line = 0
        multiline_start_col = 0

        for line_num, raw_line in enumerate(lines, start=1):
            self.line = line_num

            # Eliminar \r si existe
            line = raw_line.rstrip("\r")

            if in_multiline:
                end_idx = line.find('"""')
                if end_idx != -1:
                    # Fin del bloque multilínea en esta línea
                    multiline_lines.append(line[:end_idx])
                    content = "\n".join(multiline_lines)
                    self.tokens.append(Token(TokenType.STRING, content, multiline_start_line, multiline_start_col))
                    in_multiline = False
                    
                    # Tokenizar el resto de la linea si hay algo
                    rest = line[end_idx + 3:]
                    if rest.strip() and not rest.strip().startswith("#"):
                        self._tokenize_line(rest.strip(), line_num, offset=end_idx + 3)
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", line_num, len(line) + 1))
                else:
                    multiline_lines.append(line)
                continue

            # Línea vacía o solo espacios → ignorar
            stripped = line.strip()
            if not stripped:
                continue

            # Línea de comentario
            if stripped.startswith("#"):
                continue

            # ── Manejar indentación ──
            indent_level = len(line) - len(line.lstrip())
            current_indent = self.indent_stack[-1]

            if indent_level > current_indent:
                self.indent_stack.append(indent_level)
                self.tokens.append(Token(TokenType.INDENT, "", line_num, 1))
            elif indent_level < current_indent:
                while self.indent_stack and self.indent_stack[-1] > indent_level:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, "", line_num, 1))
                if self.indent_stack[-1] != indent_level:
                    raise LexerError("Indentación inconsistente", line_num, 1)

            # ── Tokenizar el contenido de la línea ──
            started_multiline = self._tokenize_line(stripped, line_num, offset=indent_level)
            
            if started_multiline is not None:
                in_multiline = True
                multiline_lines = [started_multiline]
                multiline_start_line = line_num
                multiline_start_col = indent_level + (len(stripped) - len(started_multiline)) + 1
            else:
                self.tokens.append(Token(TokenType.NEWLINE, "\n", line_num, len(line) + 1))

        if in_multiline:
            raise LexerError("Bloque multilínea sin cerrar al final del archivo", multiline_start_line, 1)

        # Cerrar indentaciones pendientes
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1))

        self.tokens.append(Token(TokenType.EOF, "", self.line, 1))
        return self.tokens

    def _tokenize_line(self, line: str, line_num: int, offset: int = 0) -> Optional[str]:
        """
        Tokeniza una sola línea (parcial o completa).
        Retorna el string sobrante si inicia un bloque multilínea '\"\"\"', None en otro caso.
        """
        pos = 0

        while pos < len(line):
            # Saltar espacios
            if line[pos] == " " or line[pos] == "\t":
                pos += 1
                continue

            # Comentario inline
            if line[pos] == "#":
                break

            # Asignación =
            if line[pos] == "=":
                self.tokens.append(Token(TokenType.ASSIGN, "=", line_num, offset + pos + 1))
                pos += 1
                continue

            # Variable de entorno $VAR
            if line[pos] == "$":
                start = pos
                pos += 1
                while pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                    pos += 1
                self.tokens.append(Token(TokenType.ENV_VAR, line[start + 1:pos], line_num, offset + start + 1))
                continue

            # Cadena triple """..."""
            if pos + 2 < len(line) and line[pos:pos + 3] == '"""':
                # Buscar cierre en esta misma línea
                end = line.find('"""', pos + 3)
                if end != -1:
                    self.tokens.append(Token(TokenType.STRING, line[pos + 3:end], line_num, offset + pos + 1))
                    pos = end + 3
                else:
                    return line[pos + 3:]
                continue

            # Cadena simple "..."
            if line[pos] == '"':
                start = pos
                pos += 1
                while pos < len(line) and line[pos] != '"':
                    pos += 1
                if pos < len(line):
                    pos += 1  # consumir comilla final
                self.tokens.append(Token(TokenType.STRING, line[start + 1:pos - 1], line_num, offset + start + 1))
                continue

            # Número
            if line[pos].isdigit() or (line[pos] == "-" and pos + 1 < len(line) and line[pos + 1].isdigit()):
                start = pos
                if line[pos] == "-":
                    pos += 1
                while pos < len(line) and (line[pos].isdigit() or line[pos] == "."):
                    pos += 1
                self.tokens.append(Token(TokenType.NUMBER, line[start:pos], line_num, offset + start + 1))
                continue

            # Palabra (keyword, ident, boolean)
            if line[pos].isalpha() or line[pos] == "_":
                start = pos
                while pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                    pos += 1
                word = line[start:pos]

                # Booleanos
                if word in ("true", "false"):
                    self.tokens.append(Token(TokenType.BOOLEAN, word, line_num, offset + start + 1))
                # Palabras clave
                elif word in KEYWORDS:
                    self.tokens.append(Token(TokenType.KEYWORD, word, line_num, offset + start + 1))

                    # Si es una propiedad de texto libre, capturar el resto de la línea
                    if word in FREE_TEXT_PROPERTIES:
                        # revisar que no venga un """
                        rest = line[pos:].strip()
                        if rest.startswith('"""'):
                            # Es en realidad un bloque multilínea de SQL o similar
                            pass # dejemos que la siguiente iteracion del loop consuma el """
                        elif rest:
                            self.tokens.append(Token(TokenType.TEXT, rest, line_num, offset + pos + 1))
                            pos = len(line)
                else:
                    self.tokens.append(Token(TokenType.IDENT, word, line_num, offset + start + 1))
                continue

            # Si llegamos aquí, es un carácter que no conocemos
            raise LexerError(f"Carácter inesperado: {line[pos]!r}", line_num, offset + pos + 1)
        
        return None
