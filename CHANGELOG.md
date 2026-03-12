# PEX Language Changelog

## v0.4.1 (2025-03-12) — Bug Fixes & VS Code Extension

### Bug Fixes
- Fixed parser: IdentRef now correctly extracts string value for model names with special characters
- Fixed runtime: Ollama adapter now properly resolves model names with `:` (e.g., "llama3:8b")

### VS Code Extension Improvements
- Added registered commands: pex.run, pex.check, pex.ast, pex.plan, pex.lint
- Added keybindings: Ctrl+Shift+R (run), Ctrl+Shift+C (check), Ctrl+Shift+A (ast)
- Extension now uses `pex` command instead of `python main.py`
- Added icon (PNG format)

### New Examples
- `examples/bot_vendedor_carros.pi` — Complete sales bot with 5 tasks
- `examples/inventario_carros.json` — Car inventory with 8 vehicles
- `examples/bot_vendedor_chat.py` — Standalone conversational bot
- `examples/pex_chat.py` — PEX library-based conversational bot
- `examples/ollama_test.pi` — Simple Ollama integration test

---

## v0.4.0 (2025) — Features Avanzadas

### New Features

#### Type System (Experimental)
- Type annotations for records and entities using `:` syntax
- `RecordField` and `EntityField` AST nodes with optional type information
- Parser support for `field : type` syntax

```pex
record Forecast
    revenue : float
    confidence : int
    explanation : string
```

#### Caching System
- New `pex/cache.py` module with TTL-based caching
- Automatic cache integration in runtime
- Memory blocks with configurable TTL

```pex
memory session_cache
    scope session
    ttl 60
```

#### MCP Integration
- Model Context Protocol support in `pex/adapters/mcp.py`
- Adapters for MCP tools, resources, prompts, and LLMs
- Use MCP servers as external tool providers

```pex
tool web_search
    provider mcp
    source http://localhost:8080
```

#### Static Linter
- New `pex/linter.py` module
- CLI command: `pex lint <file.pi>`
- 6 rules implemented:
  - W001: Unused variable
  - W002: Unused import
  - W003: Task without output
  - W004: Model without provider
  - W005: Empty block (no goal)
  - I001: Naming convention violation

### Improvements

#### Relative Imports
- Support for `../modules/foo` syntax
- String-based imports: `import "path/to/module"`
- Path normalization for cross-platform compatibility

#### Parser Refactoring
- Reduced code duplication with `_parse_block_properties()` helper
- Better error messages with line/column information
- Support for type annotations in records/entities

#### Runtime Enhancements
- Cache integration for task results
- MCP adapter initialization
- Cache statistics display after execution

### Tests
- +59 new tests (172 total)
- `test_cache.py`: 24 tests for caching system
- `test_mcp.py`: 17 tests for MCP adapters
- `test_linter.py`: 16 tests for linter rules

### Documentation
- Updated `README.md` with v0.4 features
- Updated `docs/architecture.md` with new components
- New examples: `cache_demo.pi`, `mcp_example.pi`

---

## v0.3.0 — Diagnostic System & Robustness

### New Features

#### Unified Diagnostic System
- `pex/diagnostics.py` with structured error reporting
- Error codes (E001-E009, W001-W004, I001-I002, L001-L004, S001-S003)
- Formatted error output with colors and suggestions

#### Import Cycle Detection
- Prevents circular imports between modules
- Clear error messages showing cycle path

#### Enhanced Error Messages
- Line and column information in all errors
- Helpful suggestions for fixing issues
- Accumulated error reporting (shows all errors, not just first)

### Improvements

#### Parser Improvements
- Robust AST typing with `ValueNode`, `TextNode`
- Better handling of multiline blocks
- Improved error recovery

#### Registry Enhancements
- Filename tracking for better error messages
- Collision detection for all block types

### Tests
- Initial test suite: 111 tests
- `test_lexer.py`: 41 tests
- `test_parser.py`: 25 tests
- `test_registry.py`: 20 tests
- `test_planner.py`: 20 tests
- `test_adapters.py`: 8 tests

### Documentation
- `docs/` directory with 7 markdown files
- Comprehensive examples in `examples/`
- Fixtures for testing in `tests/fixtures/`

---

## v0.2.0 — Runtime & Adapters

### New Features

#### Runtime Engine
- `pex/runtime.py` for program execution
- Support for real and simulated execution
- Adapter initialization and management

#### Adapters
- LLM adapters: OpenAI, Ollama
- Database adapters: SQLite, PostgreSQL
- File adapters: CSV, JSON, TXT

#### CLI Commands
- `pex run` — Execute programs
- `pex check` — Verify syntax
- `pex ast` — Display AST
- `pex plan` — Show execution plan

### Improvements

#### Execution Modes
- Check mode: Syntax and semantics only
- Run mode: Full execution with adapters
- Dry-run mode: Simulation without real calls

---

## v0.1.0 — Initial Release

### Features

#### Core Language
- Basic syntax with indentation-based blocks
- Keywords: project, task, agent, pipeline, tool, model, memory, import
- Multiline string support with `"""`

#### Parser & Lexer
- Tokenizer with Python-style indentation
- Recursive descent parser
- AST generation

#### Basic Execution
- Symbol registry
- Import resolution
- Cross-reference validation

---

## Future Roadmap

### v0.5 (Planned)
- [ ] Runtime type validation
- [ ] More linter rules
- [ ] CI/CD integration
- [ ] PyPI package publishing

### v1.0 (Vision)
- [ ] Stable type system
- [ ] Pattern matching
- [ ] Enhanced MCP support
- [ ] Performance optimizations
