"""Kling O1 Pro — image-to-video/kling-o1-pro
Docs: https://docs.freepik.com/api-reference/image-to-video/kling-o1-pro
      https://docs.freepik.com/api-reference/image-to-video/kling-o1-pro-video-reference
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
ENDPOINT = "image-to-video/kling-o1-pro"
ENDPOINT_VIDEO_REF = "image-to-video/kling-o1-pro-video-reference"
STATUS_PATH = "image-to-video/kling-o1"
RESOLUTION = "1080"
DURATIONS = ["5", "10"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/image-to-video/kling-o1-pro
    or POST /v1/ai/image-to-video/kling-o1-pro-video-reference (reference mode)
    """
    ratio_map = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    raw_ratio = params.aspect_ratio or "9:16"
    aspect = ratio_map.get(raw_ratio, raw_ratio)
    int_duration = int(params.duration or "5")

    if params.mode == "reference":
        endpoint = ENDPOINT_VIDEO_REF
        payload: dict = {
            "prompt": params.prompt,
            "aspect_ratio": aspect,
            "duration": int_duration,
        }
        refs: list[str] = []
        if params.image_base64:
            refs.append(params.image_base64)
        elif params.image_url:
            refs.append(params.image_url)
        if params.image_refs:
            refs.extend(params.image_refs)
        if refs:
            payload["reference_images"] = refs[:7]
    else:
        endpoint = ENDPOINT
        payload = {
            "prompt": params.prompt,
            "aspect_ratio": aspect,
            "duration": int_duration,
        }
        if params.image_base64:
            payload["first_frame"] = params.image_base64
        elif params.image_url:
            payload["first_frame"] = params.image_url
        if params.image_url_last:
            payload["last_frame"] = params.image_url_last
    return await send_request(endpoint, STATUS_PATH, payload)


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-o1"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_o1_pro] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-o1/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_o1_pro] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
