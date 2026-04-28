"""Kling V3 Motion Control Standard — video/kling-v3-motion-control-std
Docs: https://docs.freepik.com/api-reference/video/kling-v3-motion-control/generate-std
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "video/kling-v3-motion-control-std"
STATUS_PATH = "video/kling-v3-motion-control-std"
RESOLUTION = "720"


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/video/kling-v3-motion-control-std"""
    payload: dict = {}
    if params.prompt:
        payload["prompt"] = params.prompt
    if params.image_base64:
        payload["image_url"] = params.image_base64
    elif params.image_url:
        payload["image_url"] = params.image_url
    if params.video_url:
        payload["video_url"] = params.video_url
    payload["character_orientation"] = params.orientation or "video"
    return await send_request(ENDPOINT, STATUS_PATH, payload)


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-motion-control-std"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_v3_motion_std] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-motion-control-std/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_v3_motion_std] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
