"""
PEX Tests — Tests para el sistema de Caché.
"""

import pytest
import time
from pex.cache import Cache, CacheEntry, get_global_cache, clear_global_cache, set_global_cache


class TestCacheEntry:
    """Tests para entradas de caché."""

    def test_entry_without_ttl_never_expires(self):
        """Verifica que entrada sin TTL nunca expira."""
        entry = CacheEntry(value="test", ttl=None)
        assert not entry.is_expired()
        assert entry.remaining_seconds() == float('inf')

    def test_entry_with_ttl_expires(self):
        """Verifica que entrada con TTL expira correctamente."""
        entry = CacheEntry(value="test", ttl=1)  # 1 segundo
        assert not entry.is_expired()
        
        time.sleep(1.1)  # Esperar a que expire
        assert entry.is_expired()

    def test_entry_age(self):
        """Verifica cálculo de edad de entrada."""
        entry = CacheEntry(value="test")
        time.sleep(0.1)
        assert entry.age_seconds() >= 0.1


class TestCache:
    """Tests para el sistema de caché."""

    def test_cache_set_get(self):
        """Verifica almacenamiento y recuperación básica."""
        cache = Cache()
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """Verifica cache miss."""
        cache = Cache()
        
        assert cache.get("nonexistent") is None
        assert cache.misses == 1

    def test_cache_hit(self):
        """Verifica cache hit."""
        cache = Cache()
        cache.set("key1", "value1")
        
        cache.get("key1")
        assert cache.hits == 1

    def test_cache_hit_rate(self):
        """Verifica cálculo de hit rate."""
        cache = Cache()
        cache.set("key1", "value1")
        
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        cache.get("key1")  # hit
        
        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "66.7%"

    def test_cache_ttl(self):
        """Verifica TTL en caché."""
        cache = Cache()
        cache.set("key1", "value1", ttl=1)
        
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_default_ttl(self):
        """Verifica TTL por defecto."""
        cache = Cache(default_ttl=1)
        cache.set("key1", "value1")  # Usa TTL por defecto
        
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_get_or_set(self):
        """Verifica get_or_set."""
        cache = Cache()
        call_count = [0]
        
        def factory():
            call_count[0] += 1
            return "computed_value"
        
        # Primera llamada - computa
        result1 = cache.get_or_set("key1", factory)
        assert result1 == "computed_value"
        assert call_count[0] == 1
        
        # Segunda llamada - usa caché
        result2 = cache.get_or_set("key1", factory)
        assert result2 == "computed_value"
        assert call_count[0] == 1  # No se llama de nuevo

    def test_cache_invalidate(self):
        """Verifica invalidación de entrada."""
        cache = Cache()
        cache.set("key1", "value1")
        
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None
        assert cache.invalidate("key1") is False  # Ya no existe

    def test_cache_invalidate_pattern(self):
        """Verifica invalidación por prefijo."""
        cache = Cache()
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("product:1", "prod1")
        
        count = cache.invalidate_pattern("user:")
        assert count == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("product:1") == "prod1"

    def test_cache_clear(self):
        """Verifica limpieza completa."""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Generar hit
        
        cache.clear()
        
        assert len(cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_cache_cleanup_expired(self):
        """Verifica limpieza de entradas expiradas."""
        cache = Cache()
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=10)
        
        time.sleep(1.1)
        
        count = cache.cleanup_expired()
        assert count == 1
        assert len(cache) == 1

    def test_cache_contains(self):
        """Verifica operador in."""
        cache = Cache()
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache

    def test_cache_contains_expired(self):
        """Verifica que in retorna False para entradas expiradas."""
        cache = Cache()
        cache.set("key1", "value1", ttl=1)
        
        assert "key1" in cache
        time.sleep(1.1)
        assert "key1" not in cache


class TestGlobalCache:
    """Tests para caché global."""

    def test_get_global_cache_creates_new(self):
        """Verifica que get_global_cache crea nueva caché."""
        clear_global_cache()
        cache = get_global_cache()
        assert cache is not None
        assert isinstance(cache, Cache)

    def test_get_global_cache_returns_same(self):
        """Verifica que get_global_cache retorna misma instancia."""
        clear_global_cache()
        cache1 = get_global_cache()
        cache2 = get_global_cache()
        
        assert cache1 is cache2

    def test_set_global_cache(self):
        """Verifica que set_global_cache configura caché."""
        new_cache = Cache()
        set_global_cache(new_cache)
        
        assert get_global_cache() is new_cache

    def test_clear_global_cache(self):
        """Verifica que clear_global_cache limpia."""
        cache = get_global_cache()
        cache.set("key1", "value1")
        
        clear_global_cache()
        
        # Nueva caché está vacía
        new_cache = get_global_cache()
        assert len(new_cache) == 0


class TestCacheKeyGeneration:
    """Tests para generación de claves de caché."""

    def test_same_inputs_same_key(self):
        """Verifica que mismos inputs generan misma clave."""
        cache = Cache()
        
        key1 = cache._make_key("task1", {"a": 1}, {"b": 2})
        key2 = cache._make_key("task1", {"a": 1}, {"b": 2})
        
        assert key1 == key2

    def test_different_inputs_different_key(self):
        """Verifica que diferentes inputs generan diferente clave."""
        cache = Cache()
        
        key1 = cache._make_key("task1", {"a": 1}, {})
        key2 = cache._make_key("task1", {"a": 2}, {})
        
        assert key1 != key2

    def test_different_task_different_key(self):
        """Verifica que diferentes tasks generan diferente clave."""
        cache = Cache()
        
        key1 = cache._make_key("task1", {}, {})
        key2 = cache._make_key("task2", {}, {})
        
        assert key1 != key2

    def test_key_is_deterministic(self):
        """Verifica que clave es determinística."""
        cache = Cache()
        
        keys = [
            cache._make_key("task", {"x": 1, "y": 2}, {})
            for _ in range(10)
        ]
        
        assert len(set(keys)) == 1  # Todas iguales
