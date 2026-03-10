"""
PEX AST Utils — Utilidades para visualización y serialización del AST.
"""

import json
from dataclasses import is_dataclass, asdict
from typing import Any, Dict, List, Union
from pex.ast_nodes import Program, StringLiteral, NumberLiteral, BooleanLiteral, IdentRef, EnvVarRef

def ast_to_dict(node: Any) -> Any:
    """Convierte un nodo del AST a un diccionario serializable para JSON."""
    if node is None:
        return None
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, (str, int, float, bool)):
        return node
    
    if is_dataclass(node):
        result = {"type": type(node).__name__}
        for key, value in asdict(node).items():
            if key == "line": continue
            # Para evitar recursión infinita o redundancia, procesamos valores
            result[key] = _process_val_for_json(getattr(node, key))
        if hasattr(node, "line"):
            result["line"] = node.line
        return result
    
    return str(node)

def _process_val_for_json(val: Any) -> Any:
    if isinstance(val, list):
        return [ast_to_dict(v) for v in val]
    if is_dataclass(val):
        return ast_to_dict(val)
    return val

def print_ast(node: Any, indent: str = "", is_last: bool = True, full: bool = False):
    """Muestra una representación jerárquica y bonita del AST."""
    
    marker = "└── " if is_last else "├── "
    
    if isinstance(node, Program):
        print(f"\n{indent}Program")
        for i, stmt in enumerate(node.statements):
            print_ast(stmt, indent + "    ", i == len(node.statements) - 1, full)
        return

    # Determinamos el nombre y valor a mostrar
    node_type = type(node).__name__
    header = f"{node_type}"
    
    if hasattr(node, "name"):
        header += f"(name={repr(node.name)})"
    if hasattr(node, "line") and node.line > 0:
        header += f" [L{node.line}]"

    print(f"{indent}{marker}{header}")
    
    new_indent = indent + ("    " if is_last else "│   ")
    
    # Extraemos hijos relevantes
    children = []
    
    if hasattr(node, "value") and not isinstance(node, (StringLiteral, NumberLiteral, BooleanLiteral)):
        children.append(("value", node.value))
    
    if hasattr(node, "imports") and node.imports:
        for imp in node.imports:
            children.append(("import", f'"{imp}"'))
            
    if hasattr(node, "inputs") and node.inputs:
        for inp in node.inputs:
            children.append(("input", inp))
            
    if hasattr(node, "contexts") and node.contexts:
        for ctx in node.contexts:
            children.append(("context", ctx))
            
    if hasattr(node, "uses") and node.uses:
        for use in node.uses:
            children.append(("use", use))
            
    if hasattr(node, "steps") and node.steps:
        for step in node.steps:
            children.append(("step", step))

    # Propiedades simples
    for prop in ["model", "goal", "output", "sql", "query", "provider", "source", "model_name", "scope"]:
        if hasattr(node, prop):
            val = getattr(node, prop)
            if val is not None:
                children.append((prop, val))

    if hasattr(node, "fields") and node.fields:
        for f in node.fields:
            # fields ahora puede ser lista de RecordField/EntityField o lista de strings
            if hasattr(f, "name"):  # Es RecordField o EntityField
                if f.field_type:
                    children.append(("field", f'"{f.name}: {f.field_type}"'))
                else:
                    children.append(("field", f'"{f.name}"'))
            else:  # Es string (compatibilidad)
                children.append(("field", f'"{f}"'))

    # Imprimir hijos
    for i, (label, child) in enumerate(children):
        last_child = (i == len(children) - 1)
        c_marker = "└── " if last_child else "├── "
        
        if isinstance(child, (StringLiteral, NumberLiteral, BooleanLiteral, IdentRef, EnvVarRef)):
            val_str = _format_literal(child, full)
            print(f"{new_indent}{c_marker}{label}: {val_str}")
        elif isinstance(child, (str, int, float, bool)):
            print(f"{new_indent}{c_marker}{label}: {repr(child)}")
        else:
            # Es un nodo complejo
            print(f"{new_indent}{c_marker}{label}")
            print_ast(child, new_indent + ("    " if last_child else "│   "), True, full)

def _format_literal(node: Any, full: bool) -> str:
    t = type(node).__name__
    val = node.value if hasattr(node, "value") else node.name
    
    if isinstance(node, StringLiteral):
        text = val.replace("\n", "\\n")
        if not full and len(text) > 40:
            text = text[:37] + "..."
        return f'{t}("{text}")'
    
    return f'{t}({repr(val)})'
