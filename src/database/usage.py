from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.database.db import get_db

logger = logging.getLogger(__name__)


@dataclass
class UsageData:
    video_today: int = 0
    last_reset: str = ""
    video_month: int = 0
    last_month_reset: str = ""


class UsageManager:
    def __init__(self) -> None:
        self._cache: dict[str, UsageData] = {}

    async def get_usage(self, user_id: int | str) -> UsageData:
        uid = str(user_id)
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")

        db = await get_db()
        try:
            async with db.execute("SELECT * FROM usage WHERE user_id=?", (uid,)) as cursor:
                row = await cursor.fetchone()
        except Exception:
            row = None

        if row:
            usage = UsageData(
                video_today=row["video_today"] or 0,
                last_reset=row["last_reset"] or "",
                video_month=row["video_month"] or 0,
                last_month_reset=row["last_month_reset"] or "",
            )
        else:
            usage = UsageData()
            await db.execute(
                "INSERT OR REPLACE INTO usage (user_id, video_today, last_reset, video_month, last_month_reset) VALUES (?, 0, ?, 0, ?)",
                (uid, today, month),
            )
            await db.commit()

        if usage.last_reset != today:
            usage.video_today = 0
            usage.last_reset = today
            await db.execute("UPDATE usage SET video_today=0, last_reset=? WHERE user_id=?", (today, uid))
            await db.commit()

        if usage.last_month_reset != month:
            usage.video_month = 0
            usage.last_month_reset = month
            await db.execute("UPDATE usage SET video_month=0, last_month_reset=? WHERE user_id=?", (month, uid))
            await db.commit()

        self._cache[uid] = usage
        return usage

    async def increment_usage(self, user_id: int | str) -> None:
        uid = str(user_id)
        usage = await self.get_usage(uid)
        usage.video_today += 1
        usage.video_month += 1

        db = await get_db()
        await db.execute(
            "UPDATE usage SET video_today=?, video_month=? WHERE user_id=?",
            (usage.video_today, usage.video_month, uid),
        )
        await db.commit()

    def get_total_usage_today(self) -> int:
        return sum(u.video_today for u in self._cache.values())

    def get_total_usage_month(self) -> int:
        return sum(u.video_month for u in self._cache.values())


usage_manager = UsageManager()
