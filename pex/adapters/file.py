"""
PEX File Adapters — Lectura de archivos locales estructurados y no estructurados.
"""

import os
import csv
import json
from typing import List, Dict, Any, Union


class FileAdapter:
    """Adaptador para leer y parsear archivos locales (CSV, JSON, TXT)."""
    
    def __init__(self, source_path: str, format_type: str):
        self.source_path = source_path
        self.format_type = format_type.lower()
        self.is_configured = True
        
    def execute_query(self, query: str) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Lee el archivo según la instrucción 'query'.
        Por ahora, cualquier instrucción (ej: 'load', 'read') carga todo el archivo.
        """
        if not os.path.exists(self.source_path):
            return [{"error": f"[Error File]: No se encontró el archivo '{self.source_path}'"}]
            
        try:
            if self.format_type == "csv":
                return self._read_csv()
            elif self.format_type == "json":
                return self._read_json()
            elif self.format_type in ("txt", "md"):
                return self._read_txt()
            else:
                return [{"error": f"[Error File]: Formato '{self.format_type}' no soportado."}]
        except Exception as e:
            return [{"error": f"[Error File]: Falló la lectura de '{self.source_path}' -> {str(e)}"}]
            
    def _read_csv(self) -> List[Dict[str, Any]]:
        with open(self.source_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
            
    def _read_json(self) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        with open(self.source_path, mode='r', encoding='utf-8') as f:
            return json.load(f)
            
    def _read_txt(self) -> str:
        with open(self.source_path, mode='r', encoding='utf-8') as f:
            return f.read()
