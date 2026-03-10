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

    # ── Helpers para parseo de propiedades ────────────────────────

    def _parse_block_properties(self, block, property_map: dict, skip_keywords: list = None):
        """
        Helper genérico para parsear propiedades de bloques.

        Args:
            block: El objeto bloque a completar.
            property_map: Dict mapeando nombre de propiedad a (atributo, tipo, append).
                         Ej: {"provider": ("provider", str, False)}
            skip_keywords: Lista de keywords a ignorar (para manejo especial externo).
        """
        skip_keywords = skip_keywords or []

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break

                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value

                    # Skip keywords que se manejan externamente
                    if prop in skip_keywords:
                        self._advance()
                        self._skip_newlines()
                        continue

                    self._advance()
                    val = self._parse_value()

                    if prop in property_map:
                        attr, expected_type, is_list = property_map[prop]

                        # Validar tipo si es IdentRef requerido
                        if expected_type == IdentRef and not isinstance(val, IdentRef):
                            raise ParseError(
                                f"Se esperaba un identificador para '{prop}', se encontró {type(val).__name__}",
                                tok.line
                            )

                        # Asignar valor
                        if is_list:
                            getattr(block, attr).append(val)
                        else:
                            # Extraer valor string si es necesario
                            if expected_type == str and hasattr(val, "value"):
                                setattr(block, attr, val.value)
                            else:
                                setattr(block, attr, val)

                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

    def _parse_ident_list_property(self, block, attr: str, keyword: str):
        """Parsea una propiedad que es una lista de IdentRef (ej: steps, uses)."""
        val = self._parse_value()
        if not isinstance(val, IdentRef):
            raise ParseError(
                f"Se esperaba un identificador para '{keyword}', se encontró {type(val).__name__}",
                self._current().line
            )
        getattr(block, attr).append(val)

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
                    # Soportar tanto IDENT como STRING para imports
                    if self._current().type == TokenType.STRING:
                        mod_tok = self._advance()
                        block.imports.append(mod_tok.value)
                    else:
                        mod_tok = self._expect(TokenType.IDENT)
                        block.imports.append(mod_tok.value)
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_task(self) -> TaskBlock:
        _, name, line = self._consume_block_name()
        block = TaskBlock(name=name, line=line)

        # Mapa de propiedades para task
        property_map = {
            # (atributo, tipo esperado, es lista)
            "input": ("inputs", None, True),      # None = cualquier tipo
            "context": ("contexts", None, True),
            "use": ("uses", IdentRef, True),
            "model": ("model", IdentRef, False),
            "goal": ("goal", None, False),
            "sql": ("sql", None, False),
            "query": ("query", None, False),
        }

        if self._enter_block():
            while not self._at_block_end():
                self._skip_newlines()
                if self._at_block_end():
                    break

                tok = self._current()
                if tok.type == TokenType.KEYWORD:
                    prop = tok.value
                    self._advance()

                    # Manejo especial para output (no es lista, es string directo)
                    if prop == "output":
                        tok_out = self._expect(TokenType.IDENT)
                        block.output = tok_out.value
                        self._skip_newlines()
                        continue

                    # Usar helper para propiedades estándar
                    if prop in property_map:
                        val = self._parse_value()
                        attr, expected_type, is_list = property_map[prop]

                        # Validar tipo si es IdentRef requerido
                        if expected_type == IdentRef and not isinstance(val, IdentRef):
                            raise ParseError(
                                f"Se esperaba un identificador para '{prop}', se encontró {type(val).__name__}",
                                tok.line
                            )

                        # Asignar valor
                        if is_list:
                            getattr(block, attr).append(val)
                        else:
                            setattr(block, attr, val)

                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_agent(self) -> AgentBlock:
        _, name, line = self._consume_block_name()
        block = AgentBlock(name=name, line=line)

        property_map = {
            "goal": ("goal", None, False),
            "model": ("model", IdentRef, False),
            "use": ("uses", IdentRef, True),
        }

        self._parse_block_properties(block, property_map)
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
                    self._parse_ident_list_property(block, "steps", "step")
                    self._skip_newlines()
                else:
                    self._advance()
                    self._skip_newlines()
            self._exit_block()

        return block

    def _parse_tool(self) -> ToolBlock:
        _, name, line = self._consume_block_name()
        block = ToolBlock(name=name, line=line)

        property_map = {
            "provider": ("provider", str, False),
            "source": ("source", None, False),
        }

        self._parse_block_properties(block, property_map)
        return block

    def _parse_model(self) -> ModelBlock:
        _, name, line = self._consume_block_name()
        block = ModelBlock(name=name, line=line)

        property_map = {
            "provider": ("provider", str, False),
            "name": ("model_name", None, False),
        }

        self._parse_block_properties(block, property_map)
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

                    if prop == "scope":
                        val = self._parse_value()
                        block.scope = val.value if hasattr(val, "value") else str(val)
                    elif prop == "ttl":
                        val = self._parse_value()
                        # TTL debe ser número
                        if hasattr(val, "value"):
                            block.ttl = int(val.value) if isinstance(val.value, (int, float)) else int(val.value)
                        self._skip_newlines()
                    else:
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
                    # Campo simple o con tipo: field_name [: type]
                    field_name = tok.value
                    self._advance()

                    # Verificar si hay : tipo
                    if self._current().type == TokenType.COLON:
                        self._advance()  # consumir :
                        type_tok = self._expect(TokenType.IDENT)
                        block.add_field(field_name, type_tok.value)
                    else:
                        block.add_field(field_name)
                    self._skip_newlines()
                elif tok.type == TokenType.KEYWORD and tok.value == "field":
                    self._advance()
                    fname = self._parse_value()
                    field_name = fname.value if hasattr(fname, "value") else str(fname)

                    # Verificar si hay : tipo
                    field_type = None
                    if self._current().type == TokenType.COLON:
                        self._advance()
                        type_tok = self._expect(TokenType.IDENT)
                        field_type = type_tok.value

                    block.add_field(field_name, field_type)
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

                    if prop == "table":
                        val = self._parse_value()
                        if hasattr(val, "value"):
                            block.table = val.value
                        elif hasattr(val, "name"):
                            block.table = val.name
                        else:
                            block.table = str(val)
                    elif prop == "field":
                        # field NAME [: TYPE]
                        self._skip_newlines()
                        if self._current().type == TokenType.IDENT:
                            field_name = self._current().value
                            self._advance()
                            field_type = None

                            if self._current().type == TokenType.COLON:
                                self._advance()
                                type_tok = self._expect(TokenType.IDENT)
                                field_type = type_tok.value

                            block.add_field(field_name, field_type)
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
