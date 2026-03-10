"""
PEX Lexer — Análisis léxico del lenguaje PEX v0.3.

Convierte código fuente .pi en una secuencia de tokens,
manejando indentación al estilo Python para definir bloques.
Soporta bloques multilínea con \"\"\" reales y operadores básicos.
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

    # Operadores y Delimitadores
    ASSIGN = auto()       # =
    COMMA = auto()        # ,
    DOT = auto()          # .
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    ASTERISK = auto()     # *
    COLON = auto()        # : (para tipos)

    # Control de estructura
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()

    # Texto libre (para goal, query, etc. si no usan comillas)
    TEXT = auto()


# Palabras clave del lenguaje PEX v0.3
KEYWORDS = {
    "project", "task", "agent", "pipeline", "tool", "model", "memory",
    "import", "step", "input", "goal", "context", "output", "use",
    "provider", "name", "source", "scope", "sql", "query", "filter",
    "record", "entity", "field", "table",
}

# Propiedades que suelen aceptar texto libre
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
        self.tokens: List[Token] = []
        self.indent_stack: List[int] = [0]
        self.line_num = 0

    def tokenize(self) -> List[Token]:
        lines = self.source.splitlines()
        in_multiline = False
        multiline_content = []
        multiline_start_line = 0
        multiline_start_col = 0

        self.line_num = 0
        while self.line_num < len(lines):
            self.line_num += 1
            line = lines[self.line_num - 1].rstrip()

            if in_multiline:
                end_idx = line.find('"""')
                if end_idx != -1:
                    multiline_content.append(line[:end_idx])
                    content = "\n".join(multiline_content)
                    self.tokens.append(Token(TokenType.STRING, content, multiline_start_line, multiline_start_col))
                    in_multiline = False
                    
                    # Tokenizar el resto de la linea si hay algo
                    rest = line[end_idx + 3:].strip()
                    if rest and not rest.startswith("#"):
                        self._scan_line(rest, self.line_num, offset=end_idx + 3)
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line_num, len(line) + 1))
                else:
                    multiline_content.append(line)
                continue

            # Línea vacía o solo espacios → ignorar
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue

            # ── Manejar indentación ──
            indent_level = len(line) - len(stripped)
            current_indent = self.indent_stack[-1]

            if indent_level > current_indent:
                self.indent_stack.append(indent_level)
                self.tokens.append(Token(TokenType.INDENT, "", self.line_num, 1))
            elif indent_level < current_indent:
                while self.indent_stack and self.indent_stack[-1] > indent_level:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, "", self.line_num, 1))
                if self.indent_stack[-1] != indent_level:
                    raise LexerError("Indentación inconsistente", self.line_num, 1)

            # ── Escanear el contenido de la línea ──
            res = self._scan_line(stripped, self.line_num, offset=indent_level)
            
            if res is not None:
                in_multiline = True
                multiline_content = [res]
                multiline_start_line = self.line_num
                multiline_start_col = indent_level + (len(stripped) - len(res)) + 1
            else:
                self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line_num, len(line) + 1))

        if in_multiline:
            raise LexerError("Bloque multilínea sin cerrar al final del archivo", multiline_start_line, 1)

        # Cerrar indentaciones pendientes
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", self.line_num, 1))

        self.tokens.append(Token(TokenType.EOF, "", self.line_num, 1))
        return self.tokens

    def _scan_line(self, line: str, line_num: int, offset: int = 0) -> Optional[str]:
        """Escanea una línea. Retorna el resto si inicia un multilínea."""
        pos = 0
        while pos < len(line):
            char = line[pos]
            
            if char.isspace():
                pos += 1
                continue
            
            if char == "#":
                break
                
            # Operadores de un caracter
            if char == "=":
                self.tokens.append(Token(TokenType.ASSIGN, "=", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == ":":
                self.tokens.append(Token(TokenType.COLON, ":", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == ",":
                self.tokens.append(Token(TokenType.COMMA, ",", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == ".":
                self.tokens.append(Token(TokenType.DOT, ".", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == "(":
                self.tokens.append(Token(TokenType.LPAREN, "(", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == ")":
                self.tokens.append(Token(TokenType.RPAREN, ")", line_num, offset + pos + 1))
                pos += 1
                continue
            if char == "*":
                self.tokens.append(Token(TokenType.ASTERISK, "*", line_num, offset + pos + 1))
                pos += 1
                continue

            # Env Var $NAME
            if char == "$":
                start = pos
                pos += 1
                while pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                    pos += 1
                self.tokens.append(Token(TokenType.ENV_VAR, line[start + 1:pos], line_num, offset + start + 1))
                continue

            # String multiline """
            if line.startswith('"""', pos):
                # ¿Cierra en la misma línea?
                end = line.find('"""', pos + 3)
                if end != -1:
                    self.tokens.append(Token(TokenType.STRING, line[pos + 3:end], line_num, offset + pos + 1))
                    pos = end + 3
                    continue
                else:
                    return line[pos + 3:]

            # String single quote "
            if char == '"':
                start = pos
                pos += 1
                while pos < len(line) and line[pos] != '"':
                    pos += 1
                if pos >= len(line):
                    raise LexerError("Cadena literal sin cerrar", line_num, offset + start + 1)
                self.tokens.append(Token(TokenType.STRING, line[start + 1:pos], line_num, offset + start + 1))
                pos += 1
                continue

            # Number
            if char.isdigit() or (char == "-" and pos + 1 < len(line) and line[pos + 1].isdigit()):
                start = pos
                if char == "-": pos += 1
                while pos < len(line) and (line[pos].isdigit() or line[pos] == "."):
                    pos += 1
                self.tokens.append(Token(TokenType.NUMBER, line[start:pos], line_num, offset + start + 1))
                continue

            # Word (Keyword, Ident, Boolean)
            if char.isalpha() or char == "_":
                start = pos
                while pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                    pos += 1
                word = line[start:pos]

                if word in ("true", "false"):
                    self.tokens.append(Token(TokenType.BOOLEAN, word, line_num, offset + start + 1))
                elif word in KEYWORDS:
                    self.tokens.append(Token(TokenType.KEYWORD, word, line_num, offset + start + 1))

                    if word in FREE_TEXT_PROPERTIES:
                        # Si no hay un """ inmediato, capturamos el resto de la linea como TEXT
                        remaining = line[pos:].strip()
                        if remaining and not remaining.startswith('"""'):
                            self.tokens.append(Token(TokenType.TEXT, remaining, line_num, offset + pos + 1))
                            pos = len(line)
                else:
                    self.tokens.append(Token(TokenType.IDENT, word, line_num, offset + start + 1))
                continue
                
            raise LexerError(f"Carácter inesperado: {char!r}", line_num, offset + pos + 1)
        
        return None
