"""Kling V3 Motion Control Pro — video/kling-v3-motion-control-pro
Docs: https://docs.freepik.com/api-reference/video/kling-v3-motion-control/generate-pro
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "video/kling-v3-motion-control-pro"
STATUS_PATH = "video/kling-v3-motion-control-pro"
RESOLUTION = "1080"


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/video/kling-v3-motion-control-pro"""
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
    """GET /v1/ai/video/kling-v3-motion-control-pro"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_v3_motion_pro] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-motion-control-pro/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_v3_motion_pro] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
