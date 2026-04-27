from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    endpoint: str
    status_path: str
    needs_duration: bool
    durations: list[str] = field(default_factory=list)
    needs_orientation: bool = False
    needs_aspect_ratio: bool = False
    resolution: str = ""  # "720" for Std, "1080" for Pro


MODEL_CONFIG: dict[str, ModelConfig] = {
    "kling_v3": ModelConfig(
        endpoint="video/kling-v3-pro",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_motion": ModelConfig(
        endpoint="video/kling-v3-motion-control-pro",
        status_path="video/kling-v3-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_v3_omni": ModelConfig(
        endpoint="video/kling-v3-omni-pro",
        status_path="video/kling-v3-omni",
        needs_duration=False,
        resolution="1080",
    ),
    "kling_v3_pro": ModelConfig(
        endpoint="video/kling-v3-pro",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_std": ModelConfig(
        endpoint="video/kling-v3-std",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="720",
    ),
    "kling_v3_motion_pro": ModelConfig(
        endpoint="video/kling-v3-motion-control-pro",
        status_path="video/kling-v3-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_v3_motion_std": ModelConfig(
        endpoint="video/kling-v3-motion-control-std",
        status_path="video/kling-v3-motion-control-std",
        needs_duration=False,
        needs_orientation=True,
        resolution="720",
    ),
    "kling_v3_omni_pro": ModelConfig(
        endpoint="video/kling-v3-omni-pro",
        status_path="video/kling-v3-omni",
        needs_duration=False,
        resolution="1080",
    ),
    "kling_v3_omni_std": ModelConfig(
        endpoint="video/kling-v3-omni-std",
        status_path="video/kling-v3-omni",
        needs_duration=False,
        resolution="720",
    ),
    "kling_2_6_pro": ModelConfig(
        endpoint="image-to-video/kling-v2-6-pro",
        status_path="image-to-video/kling-v2-6",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_6_motion": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-pro",
        status_path="video/kling-v2-6-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_2_6_motion_pro": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-pro",
        status_path="video/kling-v2-6-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_2_6_motion_std": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-std",
        status_path="video/kling-v2-6-motion-control-std",
        needs_duration=False,
        needs_orientation=True,
        resolution="720",
    ),
    "kling_2_5_turbo": ModelConfig(
        endpoint="image-to-video/kling-v2-5-pro",
        status_path="image-to-video/kling-v2-5-pro",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_1_pro": ModelConfig(
        endpoint="image-to-video/kling-v2-1-pro",
        status_path="image-to-video/kling-v2-1-pro",
        needs_duration=True,
        needs_aspect_ratio=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_1": ModelConfig(
        endpoint="image-to-video/kling-v2-1-std",
        status_path="image-to-video/kling-v2-1-std",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "kling_2_1_std": ModelConfig(
        endpoint="image-to-video/kling-v2-1-std",
        status_path="image-to-video/kling-v2-1-std",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "kling_o1": ModelConfig(
        endpoint="image-to-video/kling-o1-pro",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_o1_pro": ModelConfig(
        endpoint="image-to-video/kling-o1-pro",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_o1_std": ModelConfig(
        endpoint="image-to-video/kling-o1-std",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "veo_3_1": ModelConfig(
        endpoint="text-to-video/veo-3-1",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_standard": ModelConfig(
        endpoint="text-to-video/veo-3-1",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_fast": ModelConfig(
        endpoint="text-to-video/veo-3-1-fast",
        status_path="text-to-video/veo-3-1-fast",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_ingredient": ModelConfig(
        endpoint="text-to-video/veo-3-1-ingredient",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "nano_banana_flash": ModelConfig(
        endpoint="text-to-image/nano-banana-pro-flash",
        status_path="text-to-image/nano-banana-pro-flash",
        needs_duration=False,
        needs_aspect_ratio=True,
    ),
    "nano_banana_pro": ModelConfig(
        endpoint="text-to-image/nano-banana-pro",
        status_path="text-to-image/nano-banana-pro",
        needs_duration=False,
        needs_aspect_ratio=True,
    ),
}

DEFAULT_MODELS = [
    {"id": "kling_v3", "name": "\U0001f525 Kling V3"},
    {"id": "kling_v3_motion", "name": "\U0001f525 Kling V3 Motion"},
    {"id": "kling_v3_omni", "name": "\U0001f525 Kling V3 Omni"},
    {"id": "kling_2_6_pro", "name": "\U0001f3ac Kling 2.6 Pro"},
    {"id": "kling_2_6_motion", "name": "\U0001f3ac Kling 2.6 Motion"},
    {"id": "kling_2_5_turbo", "name": "\U0001f680 Kling 2.5 Turbo"},
    {"id": "kling_2_1", "name": "\U0001f3ac Kling 2.1"},
    {"id": "kling_o1", "name": "\u2728 Kling O1"},
    {"id": "veo_3_1", "name": "\U0001f3a5 Veo 3.1"},
    {"id": "nano_banana_flash", "name": "\U0001f34c Nano Banana"},
]
