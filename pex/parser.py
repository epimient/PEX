"""
PEX Parser — Analizador sintáctico del lenguaje PEX.

Convierte la secuencia de tokens del Lexer en un Árbol Sintáctico
Abstracto (AST) siguiendo la gramática oficial de PEX v0.1.
"""

from typing import List, Optional
from pex.lexer import Token, TokenType, Lexer, LexerError
from pex.ast_nodes import (
    Program, ProjectBlock, TaskBlock, AgentBlock, PipelineBlock,
    ToolBlock, ModelBlock, MemoryBlock, RecordBlock, EntityBlock,
    Assignment, StringLiteral, NumberLiteral, BooleanLiteral,
    EnvVarRef, IdentRef,
)


class ParseError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Error de sintaxis en línea {line}: {message}")


class Parser:
    """Parser de descenso recursivo para PEX v0.1."""

    def __init__(self, tokens: List[Token], filename: str = "<stdin>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    # ── Utilidades ───────────────────────────────────────────────

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", 0, 0)

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, "", 0, 0)

    def _advance(self) -> Token:
        tok = self._current()
        self.pos += 1
        return tok

    def _expect(self, ttype: TokenType, value: str = None) -> Token:
        tok = self._current()
        if tok.type != ttype:
            raise ParseError(
                f"Se esperaba {ttype.name} pero se encontró {tok.type.name} ('{tok.value}')",
                tok.line
            )
        if value is not None and tok.value != value:
            raise ParseError(
                f"Se esperaba '{value}' pero se encontró '{tok.value}'",
                tok.line
            )
        return self._advance()

    def _skip_newlines(self):
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    def _at_block_end(self) -> bool:
        """¿Estamos al final de un bloque indentado?"""
        t = self._current().type
        return t in (TokenType.DEDENT, TokenType.EOF)

    # ── Parseo principal ─────────────────────────────────────────

    def parse(self) -> Program:
        """Punto de entrada: parsea todo el archivo .pi."""
        program = Program(filename=self.filename)

        while self._current().type != TokenType.EOF:
            self._skip_newlines()
            if self._current().type == TokenType.EOF:
                break

            stmt = self._parse_statement()
            if stmt is not None:
                program.statements.append(stmt)

        return program

    def _parse_statement(self):
        """Parsea una sentencia de nivel superior."""
        tok = self._current()

        # Asignación: IDENT = VALUE
        if tok.type == TokenType.IDENT and self._peek(1).type == TokenType.ASSIGN:
            return self._parse_assignment()

        # Bloque con keyword
        if tok.type == TokenType.KEYWORD:
            return self._parse_block(tok.value)

        # Token inesperado — avanzar para no quedarnos en bucle
        self._advance()
        return None

    # ── Asignaciones ─────────────────────────────────────────────

    def _parse_assignment(self) -> Assignment:
        name_tok = self._expect(TokenType.IDENT)
        self._expect(TokenType.ASSIGN)
        value = self._parse_value()
        self._skip_newlines()
        return Assignment(name=name_tok.value, value=value, line=name_tok.line)

    def _parse_value(self):
        """Parsea un valor literal: string, número, boolean o $ENV_VAR."""
        tok = self._current()

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(tok.value)
        elif tok.type == TokenType.NUMBER:
            self._advance()
            num = float(tok.value) if "." in tok.value else int(tok.value)
            return NumberLiteral(num)
        elif tok.type == TokenType.BOOLEAN:
            self._advance()
            return BooleanLiteral(tok.value == "true")
        elif tok.type == TokenType.ENV_VAR:
            self._advance()
            return EnvVarRef(tok.value)
        elif tok.type == TokenType.IDENT:
            self._advance()
            return IdentRef(tok.value)
        elif tok.type == TokenType.TEXT:
            self._advance()
            return StringLiteral(tok.value)
        else:
            raise ParseError(f"Valor inesperado: {tok.type.name} '{tok.value}'", tok.line)

    # ── Bloques ──────────────────────────────────────────────────

    def _parse_block(self, keyword: str):
        """Despacha al parser del bloque correspondiente."""
        parsers = {
            "project": self._parse_project,
            "task": self._parse_task,
            "agent": self._parse_agent,
            "pipeline": self._parse_pipeline,
            "tool": self._parse_tool,
            "model": self._parse_model,
            "memory": self._parse_memory,
            "record": self._parse_record,
            "entity": self._parse_entity,
        }

        parser_fn = parsers.get(keyword)
        if parser_fn:
            return parser_fn()

        # keyword desconocido como bloque de primer nivel — avanzar
        self._advance()
        return None

    def _consume_block_name(self) -> tuple:
        """Consume KEYWORD + IDENT y devuelve (keyword, name, line)."""
        kw_tok = self._advance()  # keyword
        name_tok = self._expect(TokenType.IDENT)
        self._skip_newlines()
        return kw_tok.value, name_tok.value, kw_tok.line

    def _enter_block(self) -> bool:
        """Intenta entrar en un bloque indentado. Retorna True si hay INDENT."""
        if self._current().type == TokenType.INDENT:
            self._advance()
            return True
        return False

    def _exit_block(self):
        """Sale de un bloque indentado consumiendo DEDENT."""
        self._skip_newlines()
        if self._current().type == TokenType.DEDENT:
            self._advance()

    def _read_property_value(self) -> str:
        """Lee el valor de una propiedad (ident, string, env_var, text, número)."""
        tok = self._current()
        if tok.type in (TokenType.IDENT, TokenType.STRING, TokenType.TEXT,
                        TokenType.NUMBER, TokenType.BOOLEAN):
            self._advance()
            return tok.value
        elif tok.type == TokenType.ENV_VAR:
            self._advance()
            return f"${tok.value}"
        else:
            # Capturar todo como texto si no hay token claro
            return ""

    # ── Parsers de bloques específicos ───────────────────────────

    def _parse_project(self) -> ProjectBlock:
        _, name, line = self._consume_block_name()
        block = ProjectBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD and tok.value == "import":
                    self._advance()
                    mod = self._read_property_value()
                    block.imports.append(mod)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_task(self) -> TaskBlock:
        _, name, line = self._consume_block_name()
        block = TaskBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "input":
                        block.inputs.append(val)
                    elif prop == "context":
                        block.contexts.append(val)
                    elif prop == "use":
                        block.uses.append(val)
                    elif prop == "model":
                        block.model = val
                    elif prop == "goal":
                        block.goal = val
                    elif prop == "output":
                        block.output = val
                    elif prop == "sql":
                        block.sql = val
                    elif prop == "query":
                        block.query = val
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_agent(self) -> AgentBlock:
        _, name, line = self._consume_block_name()
        block = AgentBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "goal":
                        block.goal = val
                    elif prop == "model":
                        block.model = val
                    elif prop == "use":
                        block.uses.append(val)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_pipeline(self) -> PipelineBlock:
        _, name, line = self._consume_block_name()
        block = PipelineBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD and tok.value == "step":
                    self._advance()
                    step_name = self._read_property_value()
                    block.steps.append(step_name)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_tool(self) -> ToolBlock:
        _, name, line = self._consume_block_name()
        block = ToolBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "provider":
                        block.provider = val
                    elif prop == "source":
                        block.source = val
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_model(self) -> ModelBlock:
        _, name, line = self._consume_block_name()
        block = ModelBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "provider":
                        block.provider = val
                    elif prop == "name":
                        block.model_name = val
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_memory(self) -> MemoryBlock:
        _, name, line = self._consume_block_name()
        block = MemoryBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "scope":
                        block.scope = val
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_record(self) -> RecordBlock:
        _, name, line = self._consume_block_name()
        block = RecordBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.IDENT:
                    block.fields.append(tok.value)
                    self._advance()
                    self._skip_newlines()
                elif tok.type == TokenType.KEYWORD and tok.value == "field":
                    self._advance()
                    fname = self._read_property_value()
                    block.fields.append(fname)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_entity(self) -> EntityBlock:
        _, name, line = self._consume_block_name()
        block = EntityBlock(name=name, line=line)

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break
                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()
                    val = self._read_property_value()

                    if prop == "table":
                        block.table = val
                    elif prop == "field":
                        block.fields.append(val)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block


def parse_source(source: str, filename: str = "<stdin>") -> Program:
    """Función auxiliar: tokeniza y parsea código PEX."""
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename)
    return parser.parse()


def parse_file(filepath: str) -> Program:
    """Lee y parsea un archivo .pi."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_source(source, filepath)
