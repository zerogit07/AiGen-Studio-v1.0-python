"""Job processing — submit generation + background polling via asyncio.create_task()."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from aiogram import Bot

from src.core.triple_pool import triple_pool
from src.core.types import TripleSet
from src.database.db import get_db
from src.database.members import member_manager
from src.services.freepik_api import GenerateParams, submit_generation
from src.services.polling import watch_generation

logger = logging.getLogger(__name__)


async def _upsert_job(job_id: str, user_id: int, model_id: str, status: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO jobs (job_id, user_id, model_id, status, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(job_id) DO UPDATE SET status=?""",
            (job_id, str(user_id), model_id, status, datetime.now(timezone.utc).isoformat(), status),
        )
        await db.commit()
    except Exception as exc:
        logger.error("Error upserting job: %s", exc)


async def finalize_job(
    bot: Bot,
    user_id: int,
    chat_id: int,
    prompt: str,
    model_id: str,
    state_data: dict[str, Any] | None = None,
    status_msg_id: int | None = None,
) -> None:
    state_data = state_data or {}

    triple = await triple_pool.acquire()
    if not triple:
        triple_pool.rebuild()
        triple = await triple_pool.acquire()

    if not triple:
        await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada API key/proxy yang tersedia saat ini. Coba lagi nanti.")
        return

    params = GenerateParams(
        prompt=prompt,
        model_id=model_id,
        duration=state_data.get("duration"),
        aspect_ratio=state_data.get("aspect_ratio"),
        orientation=state_data.get("orientation"),
        resolution=state_data.get("resolution"),
        image_url=state_data.get("temp_image_url"),
        image_url_last=state_data.get("temp_image_url_last"),
        image_refs=state_data.get("temp_image_refs", []),
        generate_audio=state_data.get("generate_audio", True),
        shots=state_data.get("shots", []),
        kling3_mode=state_data.get("kling3_mode"),
        camera_config=state_data.get("camera_config"),
    )

    result = await submit_generation(params, api_key=triple.api_key, proxy=triple.proxy)

    await triple_pool.release(triple)

    if "error" in result:
        error_msg = result.get("message", result.get("error", "Unknown"))
        if result.get("error") in ("burned", "dead_key"):
            await triple_pool.mark_burned(triple)
        await bot.send_message(chat_id=chat_id, text=f"\u274c Gagal submit: {error_msg}")
        await member_manager.end_process(user_id)
        return

    task_id = result.get("task_id", "")
    used_key = result.get("used_key", triple.api_key)
    status_path = result.get("final_status_path", "")

    if not task_id:
        await bot.send_message(chat_id=chat_id, text="\u274c Gagal: tidak ada task_id dari API.")
        await member_manager.end_process(user_id)
        return

    await _upsert_job(task_id, user_id, model_id, "processing")

    poll_result = await watch_generation(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        task_id=task_id,
        status_path=status_path,
        model_id=model_id,
        used_key=used_key,
        prompt=prompt,
        proxy=triple.proxy,
        status_msg_id=status_msg_id,
    )

    final_status = poll_result.get("status", "unknown")
    await _upsert_job(task_id, user_id, model_id, final_status)
    await member_manager.end_process(user_id)
