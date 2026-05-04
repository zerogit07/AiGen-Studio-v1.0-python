"""Freepik AI API router — dispatches generation requests to per-model handlers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from src.core.constants import MODEL_CONFIG
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)


@dataclass
class GenerateParams:
    prompt: str = ""
    model_id: str = ""
    duration: Optional[str] = None
    aspect_ratio: Optional[str] = None
    orientation: Optional[str] = None
    resolution: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_url_last: Optional[str] = None
    image_refs: list[str] = field(default_factory=list)
    generate_audio: bool = True
    shots: list[dict] = field(default_factory=list)
    kling3_mode: Optional[str] = None
    camera_config: Optional[dict] = None


async def submit_generation(
    params: GenerateParams,
    api_key: str = "",
    proxy: str = "",
) -> dict[str, Any]:
    config = MODEL_CONFIG.get(params.model_id)
    if not config:
        return {"error": f"Model '{params.model_id}' tidak ditemukan."}

    payload: dict[str, Any] = {"prompt": params.prompt}

    if config.needs_duration and params.duration:
        payload["duration"] = str(int(params.duration))

    if config.needs_aspect_ratio and params.aspect_ratio:
        ar_map = {
            "portrait_9_16": "9:16",
            "landscape_16_9": "16:9",
            "square_1_1": "1:1",
        }
        payload["aspect_ratio"] = ar_map.get(params.aspect_ratio, params.aspect_ratio)

    if config.needs_orientation and params.orientation:
        payload["orientation"] = params.orientation

    if params.resolution:
        payload["resolution"] = params.resolution

    if params.image_url:
        payload["start_image_url"] = params.image_url
    if params.image_url_last:
        payload["end_image_url"] = params.image_url_last
    if params.image_refs:
        payload["elements"] = [{"reference_image_urls": params.image_refs[:3]}]
    if params.generate_audio:
        payload["generate_audio"] = True

    if params.shots and params.kling3_mode in ("multi_intelligence", "multi_customize"):
        payload["multi_prompt"] = [
            {"prompt": s.get("prompt", ""), "duration": str(s.get("duration", 5))}
            for s in params.shots
        ]
        payload["multi_shot"] = True
        if params.kling3_mode == "multi_intelligence":
            payload["shot_type"] = "intelligent"
        else:
            payload["shot_type"] = "customize"

    if params.camera_config:
        payload["camera_control"] = params.camera_config

    result = await request_engine("POST", config.endpoint, payload=payload, api_key=api_key or None, proxy=proxy)

    if "error" in result:
        return result

    data = result.get("data", {})
    task_id = ""
    if isinstance(data, dict):
        task_id = str(data.get("data", {}).get("task_id", "") or data.get("task_id", ""))

    return {
        "data": data,
        "used_key": result.get("used_key", api_key),
        "final_status_path": config.status_path,
        "task_id": task_id,
    }
