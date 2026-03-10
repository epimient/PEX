"""
PEX Linter — Análisis estático de código PEX.

Proporciona reglas para detectar problemas comunes, malas prácticas
y sugerencias de mejora en archivos .pi
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class LintLevel(Enum):
    """Nivel de severidad del diagnóstico."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class LintMessage:
    """Mensaje del linter."""
    level: LintLevel
    code: str
    message: str
    file: str
    line: int
    column: Optional[int] = None
    suggestion: Optional[str] = None
    
    def format(self, use_colors: bool = True) -> str:
        """Formatea el mensaje para CLI."""
        from pex.cli import Colors
        
        level_colors = {
            LintLevel.ERROR: Colors.RED,
            LintLevel.WARNING: Colors.YELLOW,
            LintLevel.INFO: Colors.CYAN,
            LintLevel.HINT: Colors.DIM,
        }
        
        level_icons = {
            LintLevel.ERROR: "✗",
            LintLevel.WARNING: "⚠",
            LintLevel.INFO: "ℹ",
            LintLevel.HINT: "→",
        }
        
        color = level_colors.get(self.level, Colors.WHITE)
        icon = level_icons.get(self.level, "•")
        
        parts = []
        
        # Línea principal
        header = f"  {icon} "
        if use_colors:
            header += f"{color}[{self.level.value.upper()}]{Colors.RESET} "
            header += f"{Colors.DIM}{self.code}{Colors.RESET}: "
        else:
            header += f"[{self.level.value.upper()}] {self.code}: "
        
        header += self.message
        parts.append(header)
        
        # Ubicación
        location = f"     📍 {self.file}"
        if self.line > 0:
            location += f":{self.line}"
            if self.column:
                location += f":{self.column}"
        parts.append(location)
        
        # Sugerencia
        if self.suggestion:
            parts.append(f"     {Colors.DIM}💡 {self.suggestion}{Colors.RESET}")
        
        return "\n".join(parts)


class LintRule:
    """Regla de linting base."""
    
    code: str = "LINT000"
    level: LintLevel = LintLevel.WARNING
    description: str = ""
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        """
        Ejecuta la regla sobre un programa.
        
        Args:
            program: AST del programa
            registry: Registro de símbolos
        
        Returns:
            Lista de mensajes de lint
        """
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# Reglas de Linting
# ─────────────────────────────────────────────────────────────────────────────

class UnusedVariableRule(LintRule):
    """Detecta variables no usadas."""
    
    code = "W001"
    level = LintLevel.WARNING
    description = "Variable definida pero no usada"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        # Obtener todas las referencias en el programa
        all_refs = set()
        for stmt in program.statements:
            all_refs.update(self._extract_references(stmt))
        
        # Verificar variables no usadas
        for var_name in registry.variables.keys():
            if var_name not in all_refs:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Variable '{var_name}' no está siendo usada",
                    file=program.filename,
                    line=0,
                    suggestion="Eliminá la variable o usala en una task/pipeline",
                ))
        
        return messages
    
    def _extract_references(self, stmt: Any) -> set:
        """Extrae todas las referencias de un statement."""
        refs = set()
        
        # Buscar en inputs, contexts, uses, models, steps
        for attr in ['inputs', 'contexts', 'uses', 'steps']:
            if hasattr(stmt, attr):
                for item in getattr(stmt, attr):
                    if hasattr(item, 'name'):
                        refs.add(item.name)
                    elif isinstance(item, str):
                        refs.add(item)
        
        # Model
        if hasattr(stmt, 'model') and stmt.model:
            if hasattr(stmt.model, 'name'):
                refs.add(stmt.model.name)
        
        return refs


class UnusedImportRule(LintRule):
    """Detecta imports no usados."""
    
    code = "W002"
    level = LintLevel.WARNING
    description = "Import declarado pero no usado"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        # Obtener project block
        project = None
        for stmt in program.statements:
            if hasattr(stmt, 'imports'):
                project = stmt
                break
        
        if not project:
            return messages
        
        # Verificar cada import
        for imp in project.imports:
            module_name = imp if isinstance(imp, str) else getattr(imp, 'value', str(imp))
            
            # Verificar si algo del módulo se usa
            used = self._is_module_used(module_name, registry)
            
            if not used:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Import '{module_name}' no está siendo usado",
                    file=program.filename,
                    line=0,
                    suggestion="Eliminá el import si no es necesario",
                ))
        
        return messages
    
    def _is_module_used(self, module_name: str, registry: Any) -> bool:
        """Verifica si algún símbolo del módulo se usa."""
        # Los símbolos importados deberían estar en el registry
        # Verificar si se referencian en tasks/pipelines
        all_refs = set()
        
        for task in registry.tasks.values():
            all_refs.update(self._get_refs(task))
        
        for agent in registry.agents.values():
            all_refs.update(self._get_refs(agent))
        
        for pipeline in registry.pipelines.values():
            all_refs.update(self._get_refs(pipeline))
        
        # Verificar si algún símbolo del módulo se usa
        for symbol in all_refs:
            if symbol.startswith(f"{module_name}_"):
                return True
        
        return False
    
    def _get_refs(self, obj: Any) -> set:
        """Obtiene referencias de un objeto."""
        refs = set()
        for attr in ['inputs', 'contexts', 'uses', 'steps', 'model']:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if isinstance(val, list):
                    for item in val:
                        if hasattr(item, 'name'):
                            refs.add(item.name)
                elif val and hasattr(val, 'name'):
                    refs.add(val.name)
        return refs


class TaskWithoutOutputRule(LintRule):
    """Detecta tasks sin output declarado."""
    
    code = "W003"
    level = LintLevel.INFO
    description = "Task sin output declarado"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        for task_name, task in registry.tasks.items():
            if not task.output:
                # Solo warning si la task tiene model (probablemente genera algo)
                if task.model:
                    messages.append(LintMessage(
                        level=self.level,
                        code=self.code,
                        message=f"Task '{task_name}' no tiene output declarado",
                        file=program.filename,
                        line=getattr(task, 'line', 0),
                        suggestion="Considerá agregar 'output <nombre>' para reusar el resultado",
                    ))
        
        return messages


class ModelWithoutProviderRule(LintRule):
    """Detecta models sin provider explícito."""
    
    code = "W004"
    level = LintLevel.INFO
    description = "Model sin provider explícito"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        for model_name, model in registry.models.items():
            if not model.provider:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Model '{model_name}' no tiene provider explícito",
                    file=program.filename,
                    line=getattr(model, 'line', 0),
                    suggestion="Agregá 'provider openai|ollama|mcp' para claridad",
                ))
        
        return messages


class NamingConventionRule(LintRule):
    """Verifica convenciones de naming."""
    
    code = "I001"
    level = LintLevel.HINT
    description = "Convención de naming"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        # snake_case para tasks, agents, pipelines, tools, models
        snake_case_items = [
            ("task", registry.tasks),
            ("agent", registry.agents),
            ("pipeline", registry.pipelines),
            ("tool", registry.tools),
            ("model", registry.models),
        ]
        
        for kind, items in snake_case_items:
            for name in items.keys():
                if not self._is_snake_case(name):
                    messages.append(LintMessage(
                        level=self.level,
                        code=self.code,
                        message=f"{kind.capitalize()} '{name}' no sigue snake_case",
                        file=program.filename,
                        line=getattr(items[name], 'line', 0),
                        suggestion=f"Usá '{self._to_snake_case(name)}' en su lugar",
                    ))
        
        # PascalCase para records y entities
        pascal_case_items = [
            ("record", registry.records),
            ("entity", registry.entities),
        ]
        
        for kind, items in pascal_case_items:
            for name in items.keys():
                if not self._is_pascal_case(name):
                    messages.append(LintMessage(
                        level=self.level,
                        code=self.code,
                        message=f"{kind.capitalize()} '{name}' no sigue PascalCase",
                        file=program.filename,
                        line=getattr(items[name], 'line', 0),
                        suggestion=f"Usá '{self._to_pascal_case(name)}' en su lugar",
                    ))
        
        return messages
    
    def _is_snake_case(self, name: str) -> bool:
        """Verifica si es snake_case válido."""
        return bool(re.match(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$', name))
    
    def _is_pascal_case(self, name: str) -> bool:
        """Verifica si es PascalCase válido."""
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
    
    def _to_snake_case(self, name: str) -> str:
        """Convierte a snake_case (simple)."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convierte a PascalCase (simple)."""
        parts = name.replace('-', '_').split('_')
        return ''.join(p.capitalize() for p in parts)


class EmptyBlockRule(LintRule):
    """Detecta bloques vacíos o mínimos."""
    
    code = "W005"
    level = LintLevel.WARNING
    description = "Bloque vacío o mínimo"
    
    def check(self, program: Any, registry: Any) -> List[LintMessage]:
        messages = []
        
        # Tasks sin goal
        for task_name, task in registry.tasks.items():
            if not task.goal:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Task '{task_name}' no tiene goal declarado",
                    file=program.filename,
                    line=getattr(task, 'line', 0),
                    suggestion="Agregá un 'goal <descripción>' para definir la intención",
                ))
        
        # Agents sin goal
        for agent_name, agent in registry.agents.items():
            if not agent.goal:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Agent '{agent_name}' no tiene goal declarado",
                    file=program.filename,
                    line=getattr(agent, 'line', 0),
                    suggestion="Agregá un 'goal <descripción>' para definir el propósito",
                ))
        
        # Pipelines sin steps
        for pipe_name, pipe in registry.pipelines.items():
            if not pipe.steps:
                messages.append(LintMessage(
                    level=self.level,
                    code=self.code,
                    message=f"Pipeline '{pipe_name}' no tiene steps",
                    file=program.filename,
                    line=getattr(pipe, 'line', 0),
                    suggestion="Agregá al menos un 'step <task_or_agent>'",
                ))
        
        return messages


# ─────────────────────────────────────────────────────────────────────────────
# Linter Principal
# ─────────────────────────────────────────────────────────────────────────────

class Linter:
    """
    Linter principal para código PEX.
    
    Ejecuta múltiples reglas de análisis estático y reporta problemas.
    """
    
    def __init__(self):
        self.rules: List[LintRule] = [
            UnusedVariableRule(),
            UnusedImportRule(),
            TaskWithoutOutputRule(),
            ModelWithoutProviderRule(),
            NamingConventionRule(),
            EmptyBlockRule(),
        ]
        self.messages: List[LintMessage] = []
    
    def lint(self, program: Any, registry: Any) -> List[LintMessage]:
        """
        Ejecuta todas las reglas de linting.
        
        Args:
            program: AST del programa
            registry: Registro de símbolos
        
        Returns:
            Lista de mensajes de lint ordenados por severidad
        """
        self.messages = []
        
        for rule in self.rules:
            try:
                messages = rule.check(program, registry)
                self.messages.extend(messages)
            except Exception as e:
                # Si una regla falla, continuar con las demás
                self.messages.append(LintMessage(
                    level=LintLevel.INFO,
                    code="ERR",
                    message=f"Regla {rule.code} falló: {str(e)}",
                    file=program.filename,
                    line=0,
                ))
        
        # Ordenar por severidad (ERROR > WARNING > INFO > HINT)
        severity_order = {
            LintLevel.ERROR: 0,
            LintLevel.WARNING: 1,
            LintLevel.INFO: 2,
            LintLevel.HINT: 3,
        }
        
        self.messages.sort(key=lambda m: severity_order.get(m.level, 99))
        
        return self.messages
    
    def has_errors(self) -> bool:
        """Verifica si hay errores."""
        return any(m.level == LintLevel.ERROR for m in self.messages)
    
    def has_warnings(self) -> bool:
        """Verifica si hay warnings."""
        return any(m.level == LintLevel.WARNING for m in self.messages)
    
    def summary(self) -> Dict[str, int]:
        """Retorna resumen de mensajes por nivel."""
        summary = {
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "hints": 0,
        }
        
        for msg in self.messages:
            if msg.level == LintLevel.ERROR:
                summary["errors"] += 1
            elif msg.level == LintLevel.WARNING:
                summary["warnings"] += 1
            elif msg.level == LintLevel.INFO:
                summary["info"] += 1
            elif msg.level == LintLevel.HINT:
                summary["hints"] += 1
        
        return summary
    
    def format_results(self, use_colors: bool = True) -> str:
        """Formatea todos los resultados para mostrar."""
        if not self.messages:
            return ""
        
        formatted = [msg.format(use_colors) for msg in self.messages]
        return "\n\n".join(formatted)


def lint_program(program: Any, registry: Any) -> Linter:
    """
    Función convenience para lintear un programa.
    
    Args:
        program: AST del programa
        registry: Registro de símbolos
    
    Returns:
        Instancia de Linter con resultados
    """
    linter = Linter()
    linter.lint(program, registry)
    return linter
