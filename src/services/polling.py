"""Poll generation status from Freepik API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database.usage import usage_manager
from src.services.request_engine import request_engine
from src.services.stats import log_activity

logger = logging.getLogger(__name__)

POLL_INTERVAL = 10
MAX_RETRIES = 180


async def watch_generation(
    bot: Bot,
    chat_id: int,
    user_id: int,
    task_id: str,
    status_path: str,
    model_id: str,
    used_key: str,
    prompt: str = "",
    proxy: str = "",
    status_msg_id: int | None = None,
) -> dict[str, Any]:
    endpoint = f"{status_path}/{task_id}"

    for attempt in range(MAX_RETRIES):
        await asyncio.sleep(POLL_INTERVAL)
        result = await request_engine("GET", endpoint, api_key=used_key, proxy=proxy)

        if "error" in result:
            logger.warning("Polling error attempt %d: %s", attempt + 1, result.get("error"))
            continue

        data = result.get("data", {})
        inner = data.get("data", data) if isinstance(data, dict) else {}
        status = str(inner.get("status", "")).lower()

        if status in ("completed", "done", "success"):
            video_url = inner.get("video_url") or inner.get("output", {}).get("video_url", "")
            image_url = inner.get("image_url") or inner.get("output", {}).get("image_url", "")
            result_url = video_url or image_url

            if result_url:
                await usage_manager.increment_usage(user_id)
                log_activity(user_id, model_id, prompt)

                finish_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="\U0001f504 Generate Lagi", callback_data=f"finish_again:{model_id}"),
                        InlineKeyboardButton(text="\U0001f4c4 Ganti Model", callback_data="change_model"),
                    ]
                ])

                try:
                    if video_url:
                        await bot.send_video(chat_id=chat_id, video=video_url, caption=f"\u2705 Selesai!\nModel: {model_id}", reply_markup=finish_kb)
                    elif image_url:
                        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=f"\u2705 Selesai!\nModel: {model_id}", reply_markup=finish_kb)
                except Exception as exc:
                    logger.error("Error sending result: %s", exc)
                    await bot.send_message(chat_id=chat_id, text=f"\u2705 Selesai!\n\nLink: {result_url}", reply_markup=finish_kb)

                if status_msg_id:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=status_msg_id)
                    except Exception:
                        pass

                return {"status": "completed", "url": result_url}

            return {"status": "completed_no_url"}

        elif status in ("failed", "error"):
            error_msg = inner.get("error", "Unknown error")
            await bot.send_message(chat_id=chat_id, text=f"\u274c Gagal!\nError: {error_msg}")
            return {"status": "failed", "error": error_msg}

    await bot.send_message(chat_id=chat_id, text="\u23f0 Timeout: proses melebihi batas waktu (30 menit).")
    return {"status": "timeout"}
