#!/usr/bin/env python3
"""
PEX Bot Vendedor de Carros - Modo Conversacional
Este script permite chatear con el vendedor de carros de forma interactiva.
"""

import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: Se necesita el paquete 'requests'. Instálalo con: pip install requests")
    sys.exit(1)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.environ.get("PEX_MODEL", "llama3:8b")

INVENTARIO_FILE = "inventario_carros.json"

def cargar_inventario():
    """Carga el inventario de carros desde el archivo JSON."""
    try:
        with open(INVENTARIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró {INVENTARIO_FILE}")
        return []
    except json.JSONDecodeError:
        print("Error: El archivo JSON tiene formato inválido")
        return []

def formatear_inventario(inventario):
    """Formatea el inventario como texto para el prompt."""
    lineas = ["=== INVENTARIO DISPONIBLE ==="]
    for auto in inventario:
        lineas.append(f"""
🏎️ {auto['marca']} {auto['modelo']} {auto['año']}
   Precio: ${auto['precio']:,}
   Color: {auto['color']}
   Motor: {auto['motor']}
   Características: {', '.join(auto['caracteristicas'][:3])}
""")
    return "\n".join(lineas)

def consultar_ollama(system_prompt, user_prompt):
    """Consulta a Ollama."""
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get("response", "Sin respuesta")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return "Error: No se puede conectar a Ollama. ¿Está ejecutándose?"
    except requests.exceptions.Timeout:
        return "Error: Timeout esperando respuesta de Ollama"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          🚗 BOT VENDEDOR DE CARROS - CONVERSACIONAL         ║
║                  Concesionario Premium Auto                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    inventario = cargar_inventario()
    if not inventario:
        print("No hay inventario disponible. Saliendo...")
        return
    
    print(f"✅ Cargados {len(inventario)} vehículos")
    print(f"🤖 Modelo: {MODEL_NAME}")
    print("\nEscribe 'salir' para terminar la conversación")
    print("Escribe 'ver inventario' para ver todos los autos")
    print("-" * 60)
    
    inventario_texto = formatear_inventario(inventario)
    
    contexto = {
        "nombre_cliente": None,
        "presupuesto": None,
        "preferencias": [],
        "auto_seleccionado": None
    }
    
    system_prompt = f"""Eres un vendedor de carros profesional y amigable en una concesionaria de lujo llamada "Premium Auto".
Tu objetivo es ayudar al cliente a encontrar el auto perfecto.

INVENTARIO DISPONIBLE:
{inventario_texto}

INSTRUCCIONES:
1. Saluda cálidamente y pregunta el nombre del cliente
2. Pregunta qué tipo de auto busca (marca, modelo, presupuesto)
3. Recomienda opciones del inventario que coincidan
4. Sé profesional, persuasivo pero honesto
5. Cuando el cliente esté interesado, ofrece agendar una prueba de manejo
6. Incluye precio y beneficios extras (garantía, mantenimiento)
7. Usa emojis moderadamente
8. Mantén las respuestas concisas (máximo 3-4 oraciones)

RECUERDA: El cliente está en una conversación real, responde naturalmente."""

    user_prompt = "El cliente acaba de entrar a la concesionaria. Salúdalo y pregúntale cómo puedes ayudarle hoy."
    
    print("\n🤖 Bot:", end=" ")
    respuesta = consultar_ollama(system_prompt, user_prompt)
    print(respuesta)
    
    while True:
        print("\n" + "─" * 60)
        try:
            mensaje = input("👤 Tú: ").strip()
        except EOFError:
            break
        
        if not mensaje:
            continue
            
        if mensaje.lower() in ["salir", "exit", "quit"]:
            print("\n🤖 Bot: ¡Gracias por visitarnos! Que tenga un excelente día. 👋")
            break
        
        if mensaje.lower() == "ver inventario":
            print("\n" + inventario_texto)
            continue
        
        print("\n🤖 Bot:", end=" ")
        respuesta = consultar_ollama(system_prompt, mensaje)
        print(respuesta)

if __name__ == "__main__":
    main()
