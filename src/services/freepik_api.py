from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.constants import MODEL_CONFIG
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)


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


async def submit_video_generation(params: GenerateParams) -> dict:
    model_id = params.model_id
    config = MODEL_CONFIG.get(model_id)
    if not config:
        raise RuntimeError(f"Model configuration not found for: {model_id}")

    endpoint = config.endpoint
    final_status_path = config.status_path

    # Dynamically adjust category if image is provided
    if params.image_url or params.image_base64:
        if "text-to-video" in endpoint:
            endpoint = endpoint.replace("text-to-video", "image-to-video")
            final_status_path = final_status_path.replace("text-to-video", "image-to-video")
        elif "text-to-image" in endpoint:
            endpoint = endpoint.replace("text-to-image", "image-to-image")
            final_status_path = final_status_path.replace("text-to-image", "image-to-image")

    payload: dict = {}
    int_duration = int(params.duration or "5") if params.duration else 5

    # Normalize aspect ratio
    normalized_ratio = params.aspect_ratio
    if normalized_ratio == "widescreen_16_9":
        normalized_ratio = "16:9"
    elif normalized_ratio == "portrait_9_16":
        normalized_ratio = "9:16"
    elif normalized_ratio == "square_1_1":
        normalized_ratio = "1:1"

    # Build payload based on model type
    if "motion" in model_id or model_id == "kling_2_5_turbo":
        payload = {"prompt": params.prompt}
        if params.image_base64:
            payload["image"] = params.image_base64
        elif params.image_url:
            payload["image"] = params.image_url
        if "kling_2_6_motion" in model_id:
            payload["generate_audio"] = params.generate_audio
        if config.needs_orientation:
            payload["orientation"] = params.orientation or "video"
        if config.needs_duration:
            payload["duration"] = str(int_duration)

    elif "veo_3_1" in model_id or "nano_" in model_id:
        payload = {"prompt": params.prompt, "aspect_ratio": normalized_ratio}
        if "veo_3_1" in model_id:
            payload["generate_audio"] = params.generate_audio
            if params.image_url:
                payload["image"] = params.image_url
        elif "nano_" in model_id:
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

    elif "kling_o1" in model_id:
        if params.mode == "reference":
            payload = {
                "prompt": params.prompt,
                "aspect_ratio": normalized_ratio,
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
                "aspect_ratio": normalized_ratio,
                "duration": int_duration,
            }
            if params.image_base64:
                payload["first_frame"] = params.image_base64
            elif params.image_url:
                payload["first_frame"] = params.image_url
            if params.image_url_last:
                payload["last_frame"] = params.image_url_last

    elif "kling_v3" in model_id and "motion" not in model_id:
        payload = {"prompt": params.prompt}
        if config.needs_duration:
            payload["duration"] = int_duration
        if params.image_base64:
            payload["first_frame"] = params.image_base64
        elif params.image_url:
            payload["first_frame"] = params.image_url
        if params.image_url_last:
            payload["last_frame"] = params.image_url_last
        if params.image_refs:
            payload["element_images"] = params.image_refs[:3]
        if params.generate_audio:
            payload["generate_audio"] = True
        if params.shots and params.kling3_mode in ("multi_intelligence", "multi_customize"):
            payload["shots"] = [
                {"prompt": s.get("prompt", ""), "duration": s.get("duration", 5)}
                for s in params.shots
            ]
        if params.camera_config:
            payload["camera_control"] = params.camera_config

    else:
        # Kling 2.1 and others
        payload = {"prompt": params.prompt}
        if config.needs_duration:
            payload["duration"] = str(int_duration)
        if config.needs_aspect_ratio:
            payload["aspect_ratio"] = normalized_ratio
        if params.image_base64:
            payload["first_frame"] = params.image_base64
        elif params.image_url:
            payload["first_frame"] = params.image_url
        if params.generate_audio:
            payload["generate_audio"] = True

    # Add duration for veo models
    if "veo_3_1" in model_id and config.needs_duration:
        payload["duration"] = int_duration

    url = f"https://api.freepik.com/v1/ai/{endpoint}"

    try:
        result = await request_engine(
            method="POST",
            url=url,
            json_data=payload,
        )
        return {
            "data": result["data"],
            "used_key": result["used_key"],
            "final_endpoint": endpoint,
            "final_status_path": final_status_path,
            "error": None,
        }
    except RuntimeError as exc:
        error_msg = str(exc)
        if error_msg.startswith("400"):
            return {"error": error_msg, "data": None, "used_key": "", "final_endpoint": endpoint, "final_status_path": final_status_path}
        raise
