"""Nano Banana Pro — text-to-image/nano-banana-pro
Docs: https://docs.freepik.com/api-reference/text-to-image/post-nano-banana-pro
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "text-to-image/nano-banana-pro"
STATUS_PATH = "text-to-image/nano-banana-pro"


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/text-to-image/nano-banana-pro"""
    ratio_map = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    raw_ratio = params.aspect_ratio or "1:1"
    aspect = ratio_map.get(raw_ratio, raw_ratio)

    payload: dict = {"prompt": params.prompt, "aspect_ratio": aspect}
    res_map = {"4k": "4K", "2k": "2K", "1k": "1K"}
    payload["resolution"] = res_map.get(params.resolution, "2K")
    if params.image_refs:
        payload["reference_images"] = [
            {
                "image": url,
                "mime_type": (
                    "image/png"
                    if url.lower().endswith(".png")
                    else "image/webp"
                    if url.lower().endswith(".webp")
                    else "image/jpeg"
                ),
            }
            for url in params.image_refs[:3]
        ]
    return await send_request(ENDPOINT, STATUS_PATH, payload)


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/text-to-image/nano-banana-pro"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[nano_banana_pro] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/text-to-image/nano-banana-pro/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[nano_banana_pro] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
