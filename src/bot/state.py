"""User state management for multi-step workflows."""
from __future__ import annotations

import asyncio
import logging
import os
import time

from src.core.types import UserState
from src.database.users import user_manager

logger = logging.getLogger(__name__)

user_states: dict[int, UserState] = {}
ADMIN_IDS: list[int] = []


def load_admin_ids() -> None:
    raw = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS.clear()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))
    logger.info("Loaded admin IDs: %s", ADMIN_IDS)


async def get_or_create_state(
    user_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
) -> UserState:
    if user_id not in user_states:
        user_states[user_id] = UserState()
        if user_id in ADMIN_IDS:
            user_states[user_id].is_admin = True
    user_states[user_id].last_activity = int(time.time())

    await user_manager.track_user(user_id, username, first_name, last_name)
    return user_states[user_id]


def is_user_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start_state_cleaner() -> None:
    while True:
        await asyncio.sleep(300)
        now = int(time.time())
        to_remove = [uid for uid, s in user_states.items() if now - s.last_activity > 1800]
        for uid in to_remove:
            del user_states[uid]
        if to_remove:
            logger.info("Cleaned %d idle user states.", len(to_remove))
