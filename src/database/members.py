from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone, timedelta

from src.core.types import MemberData
from src.database.db import get_db

logger = logging.getLogger(__name__)


class MemberManager:
    def __init__(self) -> None:
        self._members: dict[str, MemberData] = {}
        self._in_progress_count: dict[str, int] = {}
        self._custom_limits: dict[str, dict[str, int]] = {}
        self._last_sync: dict[str, float] = {}

    async def load_members(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT * FROM members") as cursor:
                rows = await cursor.fetchall()
            for row in rows:
                uid = str(row["user_id"])
                self._members[uid] = MemberData(
                    user_id=uid,
                    plan=row["plan"] or "testing",
                    expire_date=row["expired"],
                    testing_quota=row["testing_quota"] or 0,
                    active=bool(row["active"]),
                    current_process=row["current_process"] or 0,
                )
            logger.info("Loaded %d members.", len(self._members))
        except Exception as exc:
            logger.error("Error loading members: %s", exc)

    async def load_custom_limits(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT data FROM settings WHERE id='custom_limits'") as cursor:
                row = await cursor.fetchone()
            if row and row["data"]:
                limits_data = json.loads(row["data"])
                for user_id, limits in limits_data.items():
                    if isinstance(limits, dict):
                        self._custom_limits[user_id] = {
                            k: int(v) for k, v in limits.items()
                            if isinstance(v, (int, str)) and str(v).isdigit()
                        }
            logger.info("Loaded custom limits for %d users.", len(self._custom_limits))
        except Exception as exc:
            logger.error("Error loading custom limits: %s", exc)

    async def sync_member(self, user_id: int | str) -> MemberData | None:
        uid = str(user_id)
        now = time.time()
        if uid in self._last_sync and now - self._last_sync[uid] < 60:
            return self.get_member_data(user_id)

        db = await get_db()
        try:
            self._last_sync[uid] = now
            async with db.execute("SELECT * FROM members WHERE user_id=?", (uid,)) as cursor:
                row = await cursor.fetchone()
            if row:
                existing = self._members.get(uid)
                self._members[uid] = MemberData(
                    user_id=uid,
                    plan=row["plan"] or (existing.plan if existing else "testing"),
                    expire_date=row["expired"] or (existing.expire_date if existing else None),
                    testing_quota=row["testing_quota"] if row["testing_quota"] is not None else (existing.testing_quota if existing else 0),
                    active=bool(row["active"]) if row["active"] is not None else (existing.active if existing else True),
                    current_process=row["current_process"] or (existing.current_process if existing else 0),
                )
        except Exception:
            pass
        return self.get_member_data(user_id)

    async def count_active_processes(self, user_id: int | str) -> int:
        db = await get_db()
        try:
            async with db.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE user_id=? AND status='processing'",
                (str(user_id),),
            ) as cursor:
                row = await cursor.fetchone()
            if row:
                return row["cnt"]
        except Exception:
            pass
        return self._in_progress_count.get(str(user_id), 0)

    def get_member_data(self, user_id: int | str) -> MemberData | None:
        uid = str(user_id)
        data = self._members.get(uid)
        if not data:
            return None

        now = datetime.now(timezone.utc)
        if data.expire_date:
            try:
                expire_date = datetime.fromisoformat(data.expire_date.replace("Z", "+00:00"))
            except ValueError:
                expire_date = datetime.min.replace(tzinfo=timezone.utc)
        else:
            expire_date = datetime.min.replace(tzinfo=timezone.utc)

        is_expired = now > expire_date
        diff = (expire_date - now).days
        data.is_expired = is_expired
        data.remaining_days = max(0, diff) if not is_expired else 0
        return data

    def get_all_members(self) -> dict[str, MemberData]:
        for uid in self._members:
            self.get_member_data(uid)
        return dict(self._members)

    def get_members_by_plan(self, plan: str) -> list[str]:
        return [uid for uid, m in self._members.items() if m.plan == plan]

    def get_daily_limit(self, plan: str, user_id: int | str) -> int:
        uid = str(user_id)
        if uid in self._custom_limits and "daily" in self._custom_limits[uid]:
            return self._custom_limits[uid]["daily"]
        from src.core.constants import DEFAULT_SETTINGS
        limits = {"lite": int(DEFAULT_SETTINGS["limitLite"]), "pro": int(DEFAULT_SETTINGS["limitPro"]), "ultra": int(DEFAULT_SETTINGS["limitUltra"]), "testing": 3}
        return limits.get(plan, 3)

    def get_max_process(self, plan: str, user_id: int | str) -> int:
        uid = str(user_id)
        if uid in self._custom_limits and "max_process" in self._custom_limits[uid]:
            return self._custom_limits[uid]["max_process"]
        from src.core.constants import DEFAULT_SETTINGS
        maxes = {"lite": int(DEFAULT_SETTINGS["maxLite"]), "pro": int(DEFAULT_SETTINGS["maxPro"]), "ultra": int(DEFAULT_SETTINGS["maxUltra"]), "testing": 1}
        return maxes.get(plan, 1)

    async def start_process(self, user_id: int | str, plan: str) -> bool:
        uid = str(user_id)
        active = await self.count_active_processes(user_id)
        max_p = self.get_max_process(plan, user_id)
        if active >= max_p:
            return False
        self._in_progress_count[uid] = self._in_progress_count.get(uid, 0) + 1
        return True

    async def end_process(self, user_id: int | str) -> None:
        uid = str(user_id)
        if uid in self._in_progress_count and self._in_progress_count[uid] > 0:
            self._in_progress_count[uid] -= 1

    async def add_member(self, user_id: int | str, plan: str, days: int) -> None:
        uid = str(user_id)
        now = datetime.now(timezone.utc)
        expire = (now + timedelta(days=days)).isoformat()
        testing_quota = 5 if plan == "testing" else 0

        db = await get_db()
        await db.execute(
            """INSERT INTO members (user_id, plan, expired, testing_quota, active, current_process, created_at)
               VALUES (?, ?, ?, ?, 1, 0, ?)
               ON CONFLICT(user_id) DO UPDATE SET plan=?, expired=?, testing_quota=?, active=1""",
            (uid, plan, expire, testing_quota, now.isoformat(), plan, expire, testing_quota),
        )
        await db.commit()

        self._members[uid] = MemberData(
            user_id=uid, plan=plan, expire_date=expire,
            testing_quota=testing_quota, active=True,
        )

    async def remove_member(self, user_id: int | str) -> None:
        uid = str(user_id)
        db = await get_db()
        await db.execute("DELETE FROM members WHERE user_id=?", (uid,))
        await db.commit()
        self._members.pop(uid, None)

    async def has_used_trial(self, user_id: int | str) -> bool:
        uid = str(user_id)
        db = await get_db()
        try:
            async with db.execute(
                "SELECT user_id FROM members WHERE user_id=? AND plan='testing'", (uid,)
            ) as cursor:
                return await cursor.fetchone() is not None
        except Exception:
            return False

    async def enable_all(self) -> None:
        db = await get_db()
        await db.execute("UPDATE members SET active=1")
        await db.commit()
        for m in self._members.values():
            m.active = True

    async def disable_all(self) -> None:
        db = await get_db()
        await db.execute("UPDATE members SET active=0")
        await db.commit()
        for m in self._members.values():
            m.active = False

    async def delete_all(self) -> None:
        db = await get_db()
        await db.execute("DELETE FROM members")
        await db.commit()
        self._members.clear()


member_manager = MemberManager()
