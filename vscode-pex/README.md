# PEX Language Extension for VS Code

Extensión oficial del lenguaje PEX para Visual Studio Code.

## Características

- ✅ **Syntax Highlighting** - Colores para keywords, strings, comentarios
- ✅ **Snippets** - Autocompletado para `task`, `agent`, `pipeline`, etc.
- ✅ **Comandos** - Ejecutar, checkear, ver AST/plan desde el editor
- ✅ **Asociación .pi** - Reconocimiento automático de archivos `.pi`

## Instalación

### Opción 1: Desarrollo Local

1. Abre VS Code
2. Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac)
3. Selecciona **"Extensions: Install from VSIX..."**
4. Navega a esta carpeta y selecciona

### Opción 2: Copiar a extensiones

```bash
# Copiar la carpeta a extensiones de VS Code
cp -r vscode-pex ~/.vscode/extensions/pex-language
```

### Opción 3: Empaquetar

```bash
# Instalar vsce (VS Code Extensions)
npm install -g @vscode/vsce

# Empaquetar
cd vscode-pex
vsce package

# Instalar el .vsix generado
code --install-extension pex-language-0.1.0.vsix
```

## Uso

### Syntax Highlighting

Simplemente abre un archivo `.pi` y verás los colores automáticamente.

### Snippets

Escribe el prefijo y presiona `Tab`:

| Prefijo | Expande a |
|---------|-----------|
| `task` | Bloque task completo |
| `agent` | Bloque agent |
| `pipeline` | Bloque pipeline |
| `tool` | Bloque tool |
| `model` | Bloque model |
| `memory` | Bloque memory |
| `record` | Bloque record |
| `entity` | Bloque entity |
| `project` | Bloque project |
| `sql` | Bloque SQL multilínea |

### Comandos

Desde la paleta de comandos (`Ctrl+Shift+P`):

- `PEX: Run File` - Ejecuta el archivo actual
- `PEX: Check File` - Verifica sintaxis
- `PEX: Show AST` - Muestra el árbol sintáctico
- `PEX: Show Plan` - Muestra el plan de ejecución
- `PEX: Lint File` - Analiza estáticamente

O usa el click derecho en el editor → **PEX**

## Configuración

La extensión asume que tienes PEX instalado en el proyecto. Si estás en la carpeta del proyecto PEX, los comandos funcionarán automáticamente.

## Desarrollo

```bash
# Abrir en VS Code
code vscode-pex

# Presiona F5 para abrir una nueva ventana con la extensión cargada
```

## Colores de Syntax

La gramática define estos scopes:

- `keyword.control.pex` - project, task, agent, pipeline, etc.
- `keyword.other.pex` - input, goal, output, step, etc.
- `string.quoted.double.pex` - Strings entre comillas
- `string.quoted.triple.pex` - Bloques multilínea
- `comment.line.number-sign.pex` - Comentarios con #
- `constant.numeric.pex` - Números
- `constant.language.boolean.pex` - true/false
- `variable.other.environment.pex` - Variables $ENV

## License

MIT
