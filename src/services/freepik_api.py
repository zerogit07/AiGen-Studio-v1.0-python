from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.constants import MODEL_CONFIG, ModelConfig
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"


@dataclass
class GenerateParams:
    model_id: str
    prompt: str
    aspect_ratio: str = "portrait_9_16"
    resolution: str = "720"
    duration: str = "5"
    generate_audio: bool = True
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url_last: Optional[str] = None
    image_refs: list[str] = field(default_factory=list)
    image_base64: str = ""
    mode: Optional[str] = None
    orientation: Optional[str] = None
    shots: list[dict] = field(default_factory=list)
    kling3_mode: Optional[str] = None
    camera_config: Optional[dict] = None


def _normalize_ratio(ratio: str) -> str:
    mapping = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    return mapping.get(ratio, ratio)


def _adjust_endpoint(endpoint: str, status_path: str, params: GenerateParams) -> tuple[str, str]:
    if params.image_url or params.image_base64:
        if "text-to-video" in endpoint:
            endpoint = endpoint.replace("text-to-video", "image-to-video")
            status_path = status_path.replace("text-to-video", "image-to-video")
        elif "text-to-image" in endpoint:
            endpoint = endpoint.replace("text-to-image", "image-to-image")
            status_path = status_path.replace("text-to-image", "image-to-image")
    return endpoint, status_path


async def _send_request(endpoint: str, status_path: str, payload: dict) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    try:
        result = await request_engine(method="POST", url=url, json_data=payload)
        return {
            "data": result["data"],
            "used_key": result["used_key"],
            "final_endpoint": endpoint,
            "final_status_path": status_path,
            "error": None,
        }
    except RuntimeError as exc:
        error_msg = str(exc)
        if error_msg.startswith("400"):
            return {
                "error": error_msg,
                "data": None,
                "used_key": "",
                "final_endpoint": endpoint,
                "final_status_path": status_path,
            }
        raise


# ─── Per-Model Handlers ──────────────────────────────────


async def _handle_motion(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
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
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_2_5_turbo(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    payload: dict = {}
    int_duration = int(params.duration or "5")
    if config.needs_duration:
        payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    if params.prompt:
        payload["prompt"] = params.prompt
    return await _send_request(endpoint, status_path, payload)


async def _handle_veo31(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    ratio = _normalize_ratio(params.aspect_ratio)
    int_duration = int(params.duration or "8")
    res_map = {"4k": "4k", "1080": "1080p", "720": "720p"}
    resolution = res_map.get(params.resolution, "720p")
    payload: dict = {
        "prompt": params.prompt,
        "aspect_ratio": ratio,
        "generate_audio": params.generate_audio,
        "resolution": resolution,
    }
    if config.needs_duration:
        payload["duration"] = int_duration
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    return await _send_request(endpoint, status_path, payload)


async def _handle_nano_banana(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    ratio = _normalize_ratio(params.aspect_ratio)
    payload: dict = {"prompt": params.prompt, "aspect_ratio": ratio}
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
    if params.mode:
        payload["mode"] = params.mode
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_o1(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    ratio = _normalize_ratio(params.aspect_ratio)
    int_duration = int(params.duration or "5")
    if params.mode == "reference":
        payload: dict = {
            "prompt": params.prompt,
            "aspect_ratio": ratio,
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
        payload = {
            "prompt": params.prompt,
            "aspect_ratio": ratio,
            "duration": int_duration,
        }
        if params.image_base64:
            payload["first_frame"] = params.image_base64
        elif params.image_url:
            payload["first_frame"] = params.image_url
        if params.image_url_last:
            payload["last_frame"] = params.image_url_last
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_v3(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    payload: dict = {"prompt": params.prompt}
    int_duration = int(params.duration or "5")
    if config.needs_duration:
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
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_v3_omni(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    payload: dict = {"prompt": params.prompt}
    int_duration = int(params.duration or "5")
    if config.needs_duration:
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
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_2_6_pro(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    payload: dict = {}
    int_duration = int(params.duration or "5")
    if config.needs_duration:
        payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    if params.prompt:
        payload["prompt"] = params.prompt
    if params.generate_audio:
        payload["generate_audio"] = True
    return await _send_request(endpoint, status_path, payload)


async def _handle_kling_2_1(params: GenerateParams, config: ModelConfig, endpoint: str, status_path: str) -> dict:
    payload: dict = {}
    int_duration = int(params.duration or "5")
    if config.needs_duration:
        payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    if params.image_url_last:
        payload["image_tail"] = params.image_url_last
    if params.prompt:
        payload["prompt"] = params.prompt
    return await _send_request(endpoint, status_path, payload)


# ─── Model Router ─────────────────────────────────────────


MODEL_HANDLERS = {
    "kling_v3": _handle_kling_v3,
    "kling_v3_pro": _handle_kling_v3,
    "kling_v3_std": _handle_kling_v3,
    "kling_v3_omni": _handle_kling_v3_omni,
    "kling_v3_omni_pro": _handle_kling_v3_omni,
    "kling_v3_omni_std": _handle_kling_v3_omni,
    "kling_v3_motion": _handle_motion,
    "kling_v3_motion_pro": _handle_motion,
    "kling_v3_motion_std": _handle_motion,
    "kling_2_6_pro": _handle_kling_2_6_pro,
    "kling_2_6_motion": _handle_motion,
    "kling_2_6_motion_pro": _handle_motion,
    "kling_2_6_motion_std": _handle_motion,
    "kling_2_5_turbo": _handle_kling_2_5_turbo,
    "kling_2_1": _handle_kling_2_1,
    "kling_2_1_pro": _handle_kling_2_1,
    "kling_2_1_std": _handle_kling_2_1,
    "kling_o1": _handle_kling_o1,
    "kling_o1_pro": _handle_kling_o1,
    "kling_o1_std": _handle_kling_o1,
    "veo_3_1": _handle_veo31,
    "veo_3_1_standard": _handle_veo31,
    "veo_3_1_fast": _handle_veo31,
    "veo_3_1_ingredient": _handle_veo31,
    "nano_banana_flash": _handle_nano_banana,
    "nano_banana_pro": _handle_nano_banana,
}


async def submit_video_generation(params: GenerateParams) -> dict:
    """POST - Create task (generate video/image)."""
    model_id = params.model_id
    config = MODEL_CONFIG.get(model_id)
    if not config:
        raise RuntimeError(f"Model configuration not found for: {model_id}")

    endpoint, status_path = _adjust_endpoint(config.endpoint, config.status_path, params)

    handler = MODEL_HANDLERS.get(model_id)
    if not handler:
        logger.warning("No dedicated handler for model %s, using kling_2_1 fallback", model_id)
        handler = _handle_kling_2_1

    logger.info("[%s] Submitting to %s", model_id, endpoint)
    return await handler(params, config, endpoint, status_path)


async def get_task_status(model_id: str, task_id: str, api_key: str) -> dict:
    """GET - Get single task status by task_id."""
    config = MODEL_CONFIG.get(model_id)
    if not config:
        raise RuntimeError(f"Model configuration not found for: {model_id}")

    status_path = config.status_path
    url = f"{BASE_URL}/{status_path}/{task_id}"
    logger.info("[%s] Getting task status: %s", model_id, task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)


async def list_tasks(model_id: str, api_key: str) -> dict:
    """GET - List all tasks for a model."""
    config = MODEL_CONFIG.get(model_id)
    if not config:
        raise RuntimeError(f"Model configuration not found for: {model_id}")

    status_path = config.status_path
    url = f"{BASE_URL}/{status_path}"
    logger.info("[%s] Listing all tasks", model_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
