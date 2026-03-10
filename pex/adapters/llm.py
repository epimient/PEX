"""
PEX LLM Adapters — Implementación de adaptadores para LLMs comerciales.
"""

import os
from typing import Dict, Any
from pex.adapters import LLMAdapter

class OpenAIAdapter(LLMAdapter):
    """Adaptador para el API de OpenAI utilizando el paquete oficial."""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        
        try:
            import openai
            self.api_key = os.environ.get("OPENAI_API_KEY")
            
            if self.api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.is_configured = True
            else:
                self.client = None
                self.is_configured = False
                
        except ImportError:
            self.client = None
            self.is_configured = False
            
    def execute_intent(self, goal: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        if not self.is_configured:
            return f"[Simulado] (OpenAIAdapter no configurado - falta OPENAI_API_KEY o paquete 'openai')\nMeta: {goal}"
            
        system_prompt = "You are an intelligent agent executing intention-oriented objectives.\n"
        
        if context:
            system_prompt += "\n--- CONTEXTO GLOBAL ---\n"
            for k, v in context.items():
                system_prompt += f"{k}: {v}\n"
                
        user_prompt = f"Objective: {goal}\n"
        
        if inputs:
            user_prompt += "\n--- INFORMACIÓN DE ENTRADA ---\n"
            for k, v in inputs.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    # Formatear lista de diccionarios (resultado BD probablemente)
                    import json
                    user_prompt += f"{k}:\n{json.dumps(v, default=str, indent=2)}\n"
                else:
                    user_prompt += f"{k}: {v}\n"
                    
        user_prompt += "\nProvide exactly the output required to fulfill the objective without unnecessary conversational filler."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Error LLM]: Falló ejecución OpenAI -> {str(e)}"

class OllamaAdapter(LLMAdapter):
    """Adaptador para usar modelos locales a través de Ollama."""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        
        try:
            import requests
            self.requests = requests
            self.base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            self.is_configured = True
        except ImportError:
            self.requests = None
            self.is_configured = False
            
    def execute_intent(self, goal: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        if not self.is_configured:
            return f"[Simulado] (OllamaAdapter no configurado - falta paquete 'requests')\nMeta: {goal}"
            
        system_prompt = "You are an intelligent agent executing intention-oriented objectives.\n"
        
        if context:
            system_prompt += "\n--- CONTEXTO GLOBAL ---\n"
            for k, v in context.items():
                system_prompt += f"{k}: {v}\n"
                
        user_prompt = f"Objective: {goal}\n"
        
        if inputs:
            user_prompt += "\n--- INFORMACIÓN DE ENTRADA ---\n"
            for k, v in inputs.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    import json
                    user_prompt += f"{k}:\n{json.dumps(v, default=str, indent=2)}\n"
                else:
                    user_prompt += f"{k}: {v}\n"
                    
        user_prompt += "\nProvide exactly the output required to fulfill the objective."
        
        try:
            payload = {
                "model": self.model_name or "llama3",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            }
            
            response = self.requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
            else:
                return f"[Error Ollama]: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"[Error LLM local]: Falló conexión a Ollama (¿está corriendo en {self.base_url}?) -> {str(e)}"
