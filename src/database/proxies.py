from __future__ import annotations

import asyncio
import logging
import time

import aiohttp

from src.core.types import ProxyEntry
from src.database.db import get_db

logger = logging.getLogger(__name__)


class ProxyManager:
    def __init__(self) -> None:
        self._proxies: list[ProxyEntry] = []
        self._current_index: int = 0

    async def load_proxies(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT * FROM proxies") as cursor:
                rows = await cursor.fetchall()
            self._proxies = [
                ProxyEntry(proxy=row["proxy"], active=bool(row["active"]), cooldown_until=row["cooldown_until"] or 0)
                for row in rows
            ]
            logger.info("Loaded %d proxies.", len(self._proxies))
        except Exception as exc:
            logger.error("Error loading proxies: %s", exc)

    async def add_proxy(self, proxy: str) -> None:
        if not any(p.proxy == proxy for p in self._proxies):
            self._proxies.append(ProxyEntry(proxy=proxy, active=True, cooldown_until=0))
            db = await get_db()
            await db.execute("INSERT OR REPLACE INTO proxies (proxy, active, cooldown_until) VALUES (?, 1, 0)", (proxy,))
            await db.commit()

    async def remove_proxy(self, proxy: str) -> None:
        self._proxies = [p for p in self._proxies if p.proxy != proxy]
        db = await get_db()
        await db.execute("DELETE FROM proxies WHERE proxy=?", (proxy,))
        await db.commit()

    async def toggle_proxy(self, proxy: str) -> bool:
        entry = next((p for p in self._proxies if p.proxy == proxy), None)
        if entry:
            entry.active = not entry.active
            db = await get_db()
            await db.execute("UPDATE proxies SET active=? WHERE proxy=?", (int(entry.active), proxy))
            await db.commit()
            return True
        return False

    async def enable_all(self) -> None:
        for p in self._proxies:
            p.active = True
            p.cooldown_until = 0
        db = await get_db()
        await db.execute("UPDATE proxies SET active=1, cooldown_until=0")
        await db.commit()

    async def disable_all(self) -> None:
        for p in self._proxies:
            p.active = False
        db = await get_db()
        await db.execute("UPDATE proxies SET active=0")
        await db.commit()

    async def delete_all(self) -> None:
        self._proxies.clear()
        db = await get_db()
        await db.execute("DELETE FROM proxies")
        await db.commit()

    async def check_all_proxies(self) -> dict[str, int]:
        active_count = 0
        dead_count = 0

        async def _check(p: ProxyEntry) -> bool:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://www.google.com", proxy=p.proxy, timeout=aiohttp.ClientTimeout(total=5)):
                        return True
            except Exception:
                return False

        results = await asyncio.gather(*[_check(p) for p in self._proxies])
        db = await get_db()
        for p, is_active in zip(self._proxies, results):
            p.active = is_active
            if not is_active:
                dead_count += 1
            else:
                active_count += 1
            await db.execute("UPDATE proxies SET active=? WHERE proxy=?", (int(p.active), p.proxy))
        await db.commit()
        return {"total": len(self._proxies), "active_count": active_count, "dead_count": dead_count}

    def get_all_proxies(self) -> list[ProxyEntry]:
        return self._proxies

    def get_rotated_proxy_url(self) -> str | None:
        now = int(time.time() * 1000)
        available = [p for p in self._proxies if p.active and p.cooldown_until < now]
        if not available:
            return None
        idx = self._current_index % len(available)
        self._current_index = (self._current_index + 1) % len(available)
        return available[idx].proxy


proxy_manager = ProxyManager()
