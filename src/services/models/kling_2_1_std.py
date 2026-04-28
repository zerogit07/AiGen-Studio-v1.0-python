"""Kling 2.1 Standard — image-to-video/kling-v2-1-std
Docs: https://docs.freepik.com/api-reference/image-to-video/kling-v2.1-std/
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "image-to-video/kling-v2-1-std"
STATUS_PATH = "image-to-video/kling-v2-1-std"
RESOLUTION = "720"
DURATIONS = ["5", "10"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/image-to-video/kling-v2-1-std"""
    payload: dict = {}
    int_duration = int(params.duration or "5")
    payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    if params.image_url_last:
        payload["image_tail"] = params.image_url_last
    if params.prompt:
        payload["prompt"] = params.prompt
    return await send_request(ENDPOINT, STATUS_PATH, payload)


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-v2-1-std"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_2_1_std] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-v2-1-std/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_2_1_std] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
