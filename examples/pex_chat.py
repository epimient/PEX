#!/usr/bin/env python3
"""
PEX Bot Conversacional - Usa PEX como librería para modo chat
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pex.lexer import Lexer
from pex.parser import Parser
from pex.planner import ExecutionPlanner, DiagnosticCollection
from pex.runtime import PexRuntime

def cargar_inventario(ruta="inventario_carros.json"):
    """Carga el inventario."""
    try:
        with open(ruta, "r") as f:
            return json.load(f)
    except:
        return []

def formatear_inventario(inv):
    """Formatea inventario para el prompt."""
    if not inv:
        return "No hay inventario disponible."
    
    texto = "=== INVENTARIO DE AUTOS ===\n"
    for auto in inv:
        texto += f"\n{auto['marca']} {auto['modelo']} {auto['año']}\n"
        texto += f"  Precio: ${auto['precio']:,}\n"
        texto += f"  Motor: {auto['motor']}\n"
        texto += f"  Características: {', '.join(auto['caracteristicas'][:3])}\n"
    return texto

def ejecutar_chat(mensaje_usuario, contexto=""):
    """Ejecuta una tarea de chat usando PEX."""
    
    pex_code = f"""
project chat_bot

model vendedor
   provider ollama
   name "llama3:8b"

tool inventario
   provider file
   source inventario_carros.json

task chat
   input inventario
   model vendedor
   goal Eres Alex, vendedor de Premium Auto. El cliente dice: "{mensaje_usuario}". 
   Contexto de la conversación: {contexto}
   Inventario disponible:
   {formatear_inventario(cargar_inventario())}
   
   Responde de forma natural, profesional y amigable (máximo 3 oraciones).
   Si pregunta por autos, recomienda del inventario con precio.
   Pregunta si quiere agendar prueba de manejo.
   output respuesta
"""
    
    with open("/tmp/chat_temp.pi", "w") as f:
        f.write(pex_code)
    
    try:
        with open("/tmp/chat_temp.pi", "r") as f:
            lexer = Lexer(f.read())
            tokens = lexer.tokens
            
            parser = Parser(tokens)
            program = parser.parse()
            
            diagnostics = DiagnosticCollection()
            planner = ExecutionPlanner(diagnostics)
            plan = planner.build_plan(program)
            
            if plan.has_errors():
                return "Error en el programa"
            
            runtime = PexRuntime(verbose=False)
            return runtime.execute(plan, "/tmp/chat_temp.pi")
            
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🤖 PEX BOT VENDEDOR DE CARROS - CONVERSACIONAL         ║
║                    Premium Auto                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print("✅ Cargado inventario de autos")
    print("🤖 Conectado a Ollama (llama3:8b)")
    print("\nEscribe 'salir' para terminar")
    print("-" * 60)
    
    contexto = "El cliente acaba de llegar a la concesionaria."
    
    print("\n🤖 Bot: ¡Bienvenido a Premium Auto! Soy Alex, tu asesor de ventas. ¿En qué puedo ayudarte hoy?\n")
    
    while True:
        try:
            mensaje = input("👤 Tú: ").strip()
        except EOFError:
            break
            
        if not mensaje:
            continue
            
        if mensaje.lower() in ["salir", "exit"]:
            print("\n🤖 Bot: ¡Gracias por visitarnos! Que tenga un excelente día. 👋")
            break
        
        print("\n⏳ Procesando...")
        
        try:
            resultado = ejecutar_chat(mensaje, contexto)
            print(f"\n🤖 Bot: {resultado}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
