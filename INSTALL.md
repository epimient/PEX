# PEX Language - Instalación Rápida

## Prerrequisitos

- Python 3.10 o superior
- VS Code (opcional, para IDE support)

---

## 1. Instalar PEX (Desarrollo Local)

### Opción A: Desde el repositorio

```bash
# Clonar o navegar al directorio PEX
cd /path/to/PEX

# (Opcional) Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o: .venv\Scripts\activate  # Windows

# Instalar en modo desarrollo
pip install -e .

# Verificar instalación
pex version
```

### Opción B: Usar directamente

```bash
# Sin instalar, usar directamente
python main.py version
python main.py run examples/sales_demo/project.pi
```

---

## 2. Instalar Extensión VS Code

### Método Rápido

```bash
# Copiar extensión a VS Code
cp -r vscode-pex ~/.vscode/extensions/pex-language

# Reiniciar VS Code
```

### Método Manual

1. Abre VS Code
2. Ve a `File` → `Open Folder`
3. Selecciona la carpeta `vscode-pex`
4. Presiona `F5` para ejecutar en modo desarrollo

### Método VSIX (Recomendado)

```bash
# Instalar vsce
npm install -g @vscode/vsce

# Empaquetar
cd vscode-pex
vsce package

# Instalar
code --install-extension pex-language-0.1.0.vsix
```

---

## 3. Probar la Demo

```bash
# Navegar al directorio PEX
cd /path/to/PEX

# Verificar sintaxis de la demo
python main.py check examples/sales_demo/project.pi

# Ver plan de ejecución
python main.py plan examples/sales_demo/project.pi

# Ejecutar en modo simulación
python main.py run examples/sales_demo/project.pi --dry-run

# Ejecutar con IA real (requiere OPENAI_API_KEY)
export OPENAI_API_KEY=sk-xxxxx
python main.py run examples/sales_demo/project.pi
```

---

## 4. Usar la Extensión en VS Code

1. **Abrir VS Code**
2. **Abrir carpeta PEX**: `File` → `Open Folder` → selecciona `/path/to/PEX`
3. **Abrir archivo .pi**: Navega a `examples/sales_demo/project.pi`
4. **Verificar colores**: Deberías ver syntax highlighting
5. **Probar snippets**: Escribe `task` y presiona `Tab`
6. **Ejecutar desde editor**: Click derecho → `PEX: Run File`

---

## 5. Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `pex run <file.pi>` | Ejecutar programa |
| `pex check <file.pi>` | Verificar sintaxis |
| `pex ast <file.pi>` | Mostrar AST |
| `pex plan <file.pi>` | Mostrar plan |
| `pex lint <file.pi>` | Analizar código |
| `pex version` | Mostrar versión |

---

## 6. Solución de Problemas

### "pex: command not found"

Asegúrate de que el entorno virtual esté activado:

```bash
source .venv/bin/activate  # Linux/Mac
```

O usa directamente:

```bash
python main.py run file.pi
```

### VS Code no reconoce .pi

1. Verifica que la extensión esté instalada
2. Reinicia VS Code
3. Verifica en `File` → `Preferences` → `Settings` → `Files: Associations`

### Error al ejecutar demo

Verifica tener las dependencias:

```bash
pip install -e ".[dev]"
```

---

## 7. Próximos Pasos

1. ✅ PEX instalado localmente
2. ✅ Extensión VS Code funcionando
3. ✅ Demo ejecutándose
4. 📚 Leer documentación en `docs/`
5. 🧪 Crear tu primer proyecto `.pi`

---

*PEX v0.4 — Programs intention, not implementation.*
