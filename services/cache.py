"""Tiny in-memory TTL cache."""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Simple dict-backed cache with per-entry time-to-live."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        """Return a cached value if present and not expired."""
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T) -> None:
        """Store a value with the configured TTL."""
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        """Drop all entries."""
        self._store.clear()


# Shared module-level caches used by geocoding / weather services.
geocode_cache: TTLCache[Any] = TTLCache(ttl_seconds=24 * 60 * 60)
weather_cache: TTLCache[Any] = TTLCache(ttl_seconds=10 * 60)
