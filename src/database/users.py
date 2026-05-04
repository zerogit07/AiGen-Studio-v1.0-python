from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.database.db import get_db

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self) -> None:
        self._users: set[int] = set()

    async def load_users(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT id FROM users") as cursor:
                rows = await cursor.fetchall()
            self._users = {row["id"] for row in rows}
            logger.info("Loaded %d users.", len(self._users))
        except Exception as exc:
            logger.error("Error loading users: %s", exc)

    async def track_user(self, user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> None:
        if user_id in self._users:
            return
        self._users.add(user_id)
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO users (id, username, first_name, last_name, joined_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username or "", first_name or "", last_name or "", now),
        )
        await db.commit()

    async def get_user_data(self, user_id: int) -> dict | None:
        db = await get_db()
        try:
            async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row["id"],
                    "username": row["username"],
                    "full_name": f"{row['first_name'] or ''} {row['last_name'] or ''}".strip(),
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                }
        except Exception:
            pass
        return None

    def get_all_users(self) -> list[int]:
        return list(self._users)


user_manager = UserManager()
