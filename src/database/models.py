from __future__ import annotations

import logging

from src.database.db import get_db

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self) -> None:
        self._maintenance: bool = False
        self._model_status: dict[str, bool] = {}

    async def load(self) -> None:
        db = await get_db()
        try:
            async with db.execute("SELECT * FROM models_status") as cursor:
                rows = await cursor.fetchall()
            for row in rows:
                if row["id"] == "__maintenance__":
                    self._maintenance = bool(row["active"])
                else:
                    self._model_status[row["id"]] = bool(row["active"])
            logger.info("Loaded %d model statuses. Maintenance: %s", len(self._model_status), self._maintenance)
        except Exception as exc:
            logger.error("Error loading model status: %s", exc)

    def is_maintenance(self) -> bool:
        return self._maintenance

    async def set_maintenance(self, enabled: bool) -> None:
        self._maintenance = enabled
        db = await get_db()
        await db.execute(
            "INSERT OR REPLACE INTO models_status (id, active) VALUES ('__maintenance__', ?)",
            (int(enabled),),
        )
        await db.commit()

    def is_model_active(self, model_id: str) -> bool:
        return self._model_status.get(model_id, True)

    async def toggle_model(self, model_id: str) -> bool:
        current = self._model_status.get(model_id, True)
        self._model_status[model_id] = not current
        db = await get_db()
        await db.execute(
            "INSERT OR REPLACE INTO models_status (id, active) VALUES (?, ?)",
            (model_id, int(not current)),
        )
        await db.commit()
        return not current


model_manager = ModelManager()
