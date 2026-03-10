"""
PEX Cache — Sistema de caché para resultados de ejecución.

Proporciona almacenamiento temporal de resultados con TTL (time-to-live)
para evitar re-ejecución de tareas costosas.
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Entrada de caché con valor y metadata de expiración."""
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: Optional[int] = None  # None = sin expiración
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def age_seconds(self) -> float:
        """Retorna la edad de la entrada en segundos."""
        return time.time() - self.created_at
    
    def remaining_seconds(self) -> float:
        """Retorna el tiempo restante antes de expirar."""
        if self.ttl is None:
            return float('inf')
        return max(0, (self.created_at + self.ttl) - time.time())


class Cache:
    """
    Sistema de caché en memoria para resultados de PEX.
    
    Features:
    - Almacenamiento por clave (hash de inputs + contexto)
    - TTL configurable por entrada o global
    - Invalidación automática de entradas expiradas
    - Estadísticas de hit/miss
    """
    
    def __init__(self, default_ttl: Optional[int] = None):
        """
        Inicializa la caché.
        
        Args:
            default_ttl: TTL por defecto en segundos (None = sin expiración)
        """
        self._store: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, task_name: str, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Genera una clave única para una combinación de task + inputs + contexto.
        
        Args:
            task_name: Nombre de la task
            inputs: Diccionario de inputs
            context: Diccionario de contexto
        
        Returns:
            Clave hash en formato string
        """
        # Serializar inputs y contexto de forma determinística
        data = {
            "task": task_name,
            "inputs": self._normalize(inputs),
            "context": self._normalize(context),
        }
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def _normalize(self, obj: Any) -> Any:
        """Normaliza un objeto para serialización JSON."""
        if isinstance(obj, dict):
            return {k: self._normalize(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [self._normalize(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._normalize(obj.__dict__)
        else:
            return obj
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor de la caché.
        
        Args:
            key: Clave del valor
        
        Returns:
            El valor almacenado o None si no existe o expiró
        """
        if key not in self._store:
            self.misses += 1
            return None
        
        entry = self._store[key]
        
        if entry.is_expired():
            # Eliminar entrada expirada
            del self._store[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Almacena un valor en la caché.
        
        Args:
            key: Clave del valor
            value: Valor a almacenar
            ttl: TTL en segundos (usa default_ttl si None)
        """
        actual_ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = CacheEntry(value=value, ttl=actual_ttl)
    
    def get_or_set(self, key: str, factory: callable, ttl: Optional[int] = None) -> Any:
        """
        Obtiene un valor de la caché o lo crea si no existe.
        
        Args:
            key: Clave del valor
            factory: Función que crea el valor si no existe
            ttl: TTL en segundos
        
        Returns:
            El valor almacenado (nuevo o existente)
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def invalidate(self, key: str) -> bool:
        """
        Invalida una entrada de la caché.
        
        Args:
            key: Clave a invalidar
        
        Returns:
            True si se eliminó, False si no existía
        """
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def invalidate_pattern(self, prefix: str) -> int:
        """
        Invalida todas las entradas que comienzan con un prefijo.
        
        Args:
            prefix: Prefijo de claves a invalidar
        
        Returns:
            Cantidad de entradas invalidadas
        """
        keys_to_delete = [k for k in self._store.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._store[key]
        return len(keys_to_delete)
    
    def clear(self) -> None:
        """Limpia toda la caché."""
        self._store.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self) -> int:
        """
        Limpia todas las entradas expiradas.
        
        Returns:
            Cantidad de entradas eliminadas
        """
        expired_keys = [k for k, v in self._store.items() if v.is_expired()]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la caché.
        
        Returns:
            Diccionario con hits, misses, hit_rate, size
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._store),
            "entries": [
                {
                    "key": k,
                    "age": f"{v.age_seconds():.1f}s",
                    "ttl_remaining": f"{v.remaining_seconds():.1f}s" if v.ttl is not None else "∞",
                    "expired": v.is_expired()
                }
                for k, v in list(self._store.items())[:10]  # Primeras 10 entradas
            ]
        }
    
    def __len__(self) -> int:
        """Retorna la cantidad de entradas en la caché."""
        return len(self._store)
    
    def __contains__(self, key: str) -> bool:
        """Verifica si una clave existe y no está expirada."""
        if key not in self._store:
            return False
        if self._store[key].is_expired():
            del self._store[key]
            return False
        return True


# Caché global para el runtime
_global_cache: Optional[Cache] = None


def get_global_cache() -> Cache:
    """Obtiene la caché global del runtime."""
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


def set_global_cache(cache: Cache) -> None:
    """Configura la caché global del runtime."""
    global _global_cache
    _global_cache = cache


def clear_global_cache() -> None:
    """Limpia la caché global."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
