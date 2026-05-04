from __future__ import annotations

import asyncio
import logging
import random
import time

from src.core.constants import FINGERPRINTS
from src.core.types import TripleSet
from src.database.apikeys import api_key_manager
from src.database.proxies import proxy_manager

logger = logging.getLogger(__name__)


class TriplePool:
    def __init__(self) -> None:
        self._sets: list[TripleSet] = []
        self._lock = asyncio.Lock()

    def rebuild(self) -> None:
        keys = api_key_manager.get_all_keys()
        proxies = proxy_manager.get_all_proxies()
        now = int(time.time() * 1000)

        active_keys = [k.key for k in keys if k.active and k.cooldown_until < now]
        active_proxies = [p.proxy for p in proxies if p.active and p.cooldown_until < now]

        if not active_keys:
            logger.warning("No active API keys available for TriplePool.")
        if not active_proxies:
            active_proxies = [""]

        self._sets.clear()
        for key in active_keys:
            proxy = random.choice(active_proxies) if active_proxies else ""
            fp = random.choice(FINGERPRINTS)
            self._sets.append(TripleSet(api_key=key, proxy=proxy, fingerprint=fp))

    async def acquire(self) -> TripleSet | None:
        async with self._lock:
            now = time.time()
            for ts in self._sets:
                if not ts.in_use and not ts.burned and (now - ts.last_used) > 2.0:
                    ts.in_use = True
                    ts.last_used = now
                    return ts
            # try any non-burned
            for ts in self._sets:
                if not ts.in_use and not ts.burned:
                    ts.in_use = True
                    ts.last_used = now
                    return ts
        return None

    async def release(self, triple: TripleSet) -> None:
        async with self._lock:
            triple.in_use = False

    async def mark_burned(self, triple: TripleSet) -> None:
        async with self._lock:
            triple.burned = True
            triple.in_use = False
            await api_key_manager.set_cooldown(triple.api_key, 1800)
            logger.warning("TripleSet burned: key=%s...", triple.api_key[:12])

    def __len__(self) -> int:
        return len(self._sets)


triple_pool = TriplePool()
