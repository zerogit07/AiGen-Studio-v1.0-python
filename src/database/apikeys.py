from __future__ import annotations

import logging
import random
import time

from src.core.types import ApiKey
from src.database.db import get_db

logger = logging.getLogger(__name__)


class ApiKeyManager:
    def __init__(self) -> None:
        self._keys: list[ApiKey] = []
        self._current_index: int = 0

    async def load_keys(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT * FROM api_keys") as cursor:
                rows = await cursor.fetchall()
            self._keys = [
                ApiKey(key=row["key"], active=bool(row["active"]), cooldown_until=row["cooldown_until"] or 0)
                for row in rows
            ]
            logger.info("Loaded %d API keys.", len(self._keys))
        except Exception as exc:
            logger.error("Error loading keys: %s", exc)

    def get_all_keys(self) -> list[ApiKey]:
        return self._keys

    def get_shuffled_active_keys(self) -> list[str]:
        now = int(time.time() * 1000)
        active = [k.key for k in self._keys if k.active and k.cooldown_until < now]
        random.shuffle(active)
        return active

    def get_rotated_keys(self) -> list[ApiKey]:
        now = int(time.time() * 1000)
        available = [k for k in self._keys if k.active and k.cooldown_until < now]
        if not available:
            return []
        sorted_keys = list(self._keys)
        rotated: list[ApiKey] = []
        for i in range(len(sorted_keys)):
            idx = (self._current_index + i) % len(sorted_keys)
            k = sorted_keys[idx]
            if k.active and k.cooldown_until < now:
                rotated.append(k)
        return rotated

    def update_index(self) -> None:
        if self._keys:
            self._current_index = (self._current_index + 1) % len(self._keys)

    async def set_cooldown(self, key: str, custom_duration_seconds: int | None = None) -> None:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            duration = (custom_duration_seconds * 1000 if custom_duration_seconds else random.randint(60, 120) * 1000)
            ak.cooldown_until = int(time.time() * 1000) + duration
            db = await get_db()
            await db.execute("UPDATE api_keys SET cooldown_until=? WHERE key=?", (ak.cooldown_until, key))
            await db.commit()

    async def mark_key_dead(self, key: str) -> None:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            ak.active = False
            db = await get_db()
            await db.execute("UPDATE api_keys SET active=0 WHERE key=?", (key,))
            await db.commit()

    async def add_key(self, key: str) -> None:
        if not any(ak.key == key for ak in self._keys):
            self._keys.append(ApiKey(key=key, active=True, cooldown_until=0))
            db = await get_db()
            await db.execute(
                "INSERT OR REPLACE INTO api_keys (key, active, cooldown_until) VALUES (?, 1, 0)", (key,)
            )
            await db.commit()

    async def remove_key(self, key: str) -> None:
        self._keys = [ak for ak in self._keys if ak.key != key]
        db = await get_db()
        await db.execute("DELETE FROM api_keys WHERE key=?", (key,))
        await db.commit()

    async def toggle_key(self, key: str) -> bool:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            ak.active = not ak.active
            db = await get_db()
            await db.execute("UPDATE api_keys SET active=? WHERE key=?", (int(ak.active), key))
            await db.commit()
            return True
        return False

    async def enable_all(self) -> None:
        for k in self._keys:
            k.active = True
            k.cooldown_until = 0
        db = await get_db()
        await db.execute("UPDATE api_keys SET active=1, cooldown_until=0")
        await db.commit()

    async def disable_all(self) -> None:
        for k in self._keys:
            k.active = False
        db = await get_db()
        await db.execute("UPDATE api_keys SET active=0")
        await db.commit()

    async def delete_all(self) -> None:
        self._keys.clear()
        db = await get_db()
        await db.execute("DELETE FROM api_keys")
        await db.commit()


api_key_manager = ApiKeyManager()
