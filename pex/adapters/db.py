"""
PEX DB Adapters — Implementación de adaptadores para Bases de Datos relacionales.
"""

from typing import List, Dict, Any
from pex.adapters import DBAdapter

class SQLiteAdapter(DBAdapter):
    """Adaptador para bases de datos SQLite."""
    
    def __init__(self, source_url: str):
        super().__init__(source_url)
        # source_url debería ser el path al archivo sqlite
        
        try:
            import sqlite3
            self.module = sqlite3
            self.is_configured = True
        except ImportError:
            self.module = None
            self.is_configured = False
            
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return [{"error": "[Simulado] SQLite DBAdapter no configurado."}]
            
        try:
            # Eliminar prefijos sqlite:// si existen
            db_path = self.source_url.replace("sqlite://", "").replace("sqlite:///", "")
            
            with self.module.connect(db_path) as conn:
                conn.row_factory = self.module.Row
                cursor = conn.cursor()
                cursor.execute(sql)
                
                rows = cursor.fetchall()
                # Convertir sqlite3.Row a dict
                return [dict(row) for row in rows]
                
        except Exception as e:
            return [{"error": f"[Error DB SQLite]: {str(e)}"}]


class PostgresAdapter(DBAdapter):
    """Adaptador para bases de datos PostgreSQL."""
    
    def __init__(self, source_url: str):
        super().__init__(source_url)
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.module = psycopg2
            self.cursor_factory = RealDictCursor
            self.is_configured = True
        except ImportError:
            self.module = None
            self.cursor_factory = None
            self.is_configured = False
            
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return [{"error": "[Simulado] Postgres DBAdapter no configurado (falta psycopg2-binary)."}]
            
        try:
            with self.module.connect(self.source_url) as conn:
                with conn.cursor(cursor_factory=self.cursor_factory) as cursor:
                    cursor.execute(sql)
                    
                    if cursor.description:
                        rows = cursor.fetchall()
                        # RealDictRow se comporta casi como dict, pero es mejor forzarlo
                        return [dict(row) for row in rows]
                    else:
                        conn.commit()
                        return [{"status": "success", "rows_affected": cursor.rowcount}]
                        
        except Exception as e:
            return [{"error": f"[Error DB Postgres]: {str(e)}"}]
