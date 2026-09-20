# time-based LRU cache using OrderedDict to minimize fetch calls to Alchemy

from collections import OrderedDict
import time
from typing import Any, Optional

class TTLCache:
    """ 
    constructor that initializes the values and ensure max size
    max_size: maximum number of entries before LRU algorithm starts
    ttl_seconds: default time to live for entries that do not set their own TTL
    """
    def __init__(self, max_size: int = 100, ttl_seconds: float = 60):

        if max_size <= 0:
            raise ValueError("max size is negative")

        if ttl_seconds <= 0:
            raise ValueError("ttl seconds is negative")

        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # key : (value, expires_at)
        # expires_at is an monotonic timestamp, can be compared to time.monotonic()
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0


    def _remove_expired(self) -> None:
        """
        Goes through entire self._store and drops all entries past expiration
        Called in set() so never grows past max_size with expired entries
        """

        now = time.monotonic()

        expired_keys = [key for key, (_, expires_at) in self._store.items() if now >= expires_at]

        for key in expired_keys:
            del self._store[key]

    def get(self, key) -> Optional[Any]:
        """
        Returns cached value or None if miss
        A 'hit' marks the key as most recently used using OrderedDict function move_to_end()
        """
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None

        value, expires_at = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            self.misses += 1
            return None

        self._store.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Stores value under key, expiring after ttl_seconds
        If cache is at max_size after inserting it evicts LRU entry
        """

        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds

        if ttl <= 0:
            raise ValueError("ttl_seconds must be positive")

        self._remove_expired()

        self._store[key] = (value, time.monotonic() + ttl)
        self._store.move_to_end(key)

        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def stats(self) -> dict[str, int | float]:

        """ Returns a snapshot of cache performance for testing functionality """

        self._remove_expired()
        total = self.hits + self.misses

        return {
            "size": len(self._store),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total else 0.0,
        }
