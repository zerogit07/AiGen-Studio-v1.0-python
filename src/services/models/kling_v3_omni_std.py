"""Kling V3 Omni Standard — video/kling-v3-omni-std
Docs: https://docs.freepik.com/api-reference/video/kling-v3-omni/generate-std
Response codes: 200, 400, 401, 500, 503
Note: multi_prompt is string[] (NOT object[] like V3)
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "video/kling-v3-omni-std"
STATUS_PATH = "video/kling-v3-omni"
RESOLUTION = "720"
DURATIONS = ["3", "5", "7", "10", "12", "15"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/video/kling-v3-omni-std"""
    payload: dict = {"prompt": params.prompt}
    int_duration = int(params.duration or "5")
    payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["start_image_url"] = params.image_base64
    elif params.image_url:
        payload["start_image_url"] = params.image_url
    if params.image_url_last:
        payload["end_image_url"] = params.image_url_last
    if params.image_refs:
        payload["elements"] = [
            {"reference_image_urls": params.image_refs[:3]}
        ]
    if params.generate_audio:
        payload["generate_audio"] = True
    if params.shots and params.kling3_mode in ("multi_intelligence", "multi_customize"):
        payload["multi_prompt"] = [
            s.get("prompt", "") for s in params.shots
        ]
        if params.kling3_mode == "multi_intelligence":
            payload["shot_type"] = "intelligent"
        else:
            payload["shot_type"] = "customize"
    return await send_request(ENDPOINT, STATUS_PATH, payload)


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-omni"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_v3_omni_std] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-omni/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_v3_omni_std] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
