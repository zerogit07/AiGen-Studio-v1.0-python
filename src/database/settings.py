from __future__ import annotations

import json
import logging

from src.core.constants import DEFAULT_SETTINGS
from src.database.db import get_db

logger = logging.getLogger(__name__)


class LandingPageManager:
    def __init__(self) -> None:
        self._data: dict[str, str] = dict(DEFAULT_SETTINGS)

    async def load_settings(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT data FROM settings WHERE id='landing_page'") as cursor:
                row = await cursor.fetchone()
            if row and row["data"]:
                stored = json.loads(row["data"])
                if isinstance(stored, dict):
                    self._data.update(stored)
            logger.info("Landing page settings loaded.")
        except Exception:
            logger.info("No stored settings found, using defaults.")

    def get_setting(self, key: str) -> str:
        return self._data.get(key, DEFAULT_SETTINGS.get(key, ""))

    async def update_setting(self, key: str, value: str) -> None:
        self._data[key] = value
        db = await get_db()
        await db.execute(
            "INSERT OR REPLACE INTO settings (id, data) VALUES ('landing_page', ?)",
            (json.dumps(self._data),),
        )
        await db.commit()


landing_page_manager = LandingPageManager()
