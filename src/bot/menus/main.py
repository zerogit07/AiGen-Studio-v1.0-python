"""Main bot menus and model config keyboards."""
from __future__ import annotations

import math
from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.constants import DEFAULT_MODELS
from src.core.types import UserState


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for model in DEFAULT_MODELS:
        rows.append([InlineKeyboardButton(text=model["name"], callback_data=f"model:{model['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_kling21_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "\U0001f3ac *Kling 2.1 Config*\n\n"
        f"Resolusi: *{state.resolution or '720'}*\n"
        f"Durasi: *{state.duration or '5'}s*\n"
        f"Aspect Ratio: *{state.aspect_ratio or 'portrait_9_16'}*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="720", callback_data="k21_res:720"),
            InlineKeyboardButton(text="1080", callback_data="k21_res:1080"),
        ],
        [
            InlineKeyboardButton(text="5s", callback_data="k21_dur:5"),
            InlineKeyboardButton(text="10s", callback_data="k21_dur:10"),
        ],
        [
            InlineKeyboardButton(text="9:16", callback_data="k21_rat:portrait_9_16"),
            InlineKeyboardButton(text="16:9", callback_data="k21_rat:landscape_16_9"),
            InlineKeyboardButton(text="1:1", callback_data="k21_rat:square_1_1"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="k21_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_kling26_pro_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "\U0001f3ac *Kling 2.6 Pro Config*\n\n"
        f"Resolusi: *{state.resolution or '1080'}*\n"
        f"Durasi: *{state.duration or '5'}s*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="720", callback_data="k26p_res:720"),
            InlineKeyboardButton(text="1080", callback_data="k26p_res:1080"),
        ],
        [
            InlineKeyboardButton(text="5s", callback_data="k26p_dur:5"),
            InlineKeyboardButton(text="10s", callback_data="k26p_dur:10"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="k26p_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_kling25_turbo_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "\U0001f680 *Kling 2.5 Turbo Config*\n\n"
        f"Resolusi: *{state.resolution or '1080'}*\n"
        f"Durasi: *{state.duration or '5'}s*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="720", callback_data="k25t_res:720"),
            InlineKeyboardButton(text="1080", callback_data="k25t_res:1080"),
        ],
        [
            InlineKeyboardButton(text="5s", callback_data="k25t_dur:5"),
            InlineKeyboardButton(text="10s", callback_data="k25t_dur:10"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="k25t_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_kling26_motion_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "\U0001f3ac *Kling 2.6 Motion Config*\n\n"
        f"Orientation: *{state.orientation or 'video'}*\n"
        f"Resolusi: *{state.resolution or '720'}*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Video", callback_data="k26m_ori:video"),
            InlineKeyboardButton(text="Photo", callback_data="k26m_ori:photo"),
        ],
        [
            InlineKeyboardButton(text="720", callback_data="k26m_res:720"),
            InlineKeyboardButton(text="1080", callback_data="k26m_res:1080"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="k26m_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_veo31_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    is_standard = state.model == "veo_3_1_standard"
    text = (
        "\U0001f3a5 *Veo 3.1 Config*\n\n"
        f"Mode: *{'Standard' if is_standard else 'Fast'}*\n"
        f"Resolusi: *{state.resolution or '720'}*\n"
        f"Aspect Ratio: *{state.aspect_ratio or 'portrait_9_16'}*\n"
        f"Durasi: *{state.duration or '8'}s*\n"
        f"Audio: *{'On' if state.generate_audio else 'Off'}*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Fast", callback_data="veo31_mod:fast"),
            InlineKeyboardButton(text="Standard", callback_data="veo31_mod:standard"),
        ],
        [
            InlineKeyboardButton(text="720", callback_data="veo31_res:720"),
            InlineKeyboardButton(text="1080", callback_data="veo31_res:1080"),
        ],
        [
            InlineKeyboardButton(text="9:16", callback_data="veo31_rat:portrait_9_16"),
            InlineKeyboardButton(text="16:9", callback_data="veo31_rat:landscape_16_9"),
            InlineKeyboardButton(text="1:1", callback_data="veo31_rat:square_1_1"),
        ],
        [
            InlineKeyboardButton(text="4s", callback_data="veo31_dur:4"),
            InlineKeyboardButton(text="6s", callback_data="veo31_dur:6"),
            InlineKeyboardButton(text="8s", callback_data="veo31_dur:8"),
        ],
        [
            InlineKeyboardButton(text="Audio On", callback_data="veo31_aud:on"),
            InlineKeyboardButton(text="Audio Off", callback_data="veo31_aud:off"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="veo31_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_nano_banana_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    is_pro = state.model == "nano_banana_pro"
    text = (
        "\U0001f34c *Nano Banana Config*\n\n"
        f"Mode: *{'Pro' if is_pro else 'Flash'}*\n"
        f"Resolusi: *{state.resolution or '1k'}*\n"
        f"Aspect Ratio: *{state.aspect_ratio or 'portrait_9_16'}*\n\n"
        "Pilih konfigurasi di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Flash", callback_data="nano_mod:flash"),
            InlineKeyboardButton(text="Pro", callback_data="nano_mod:pro"),
        ],
        [
            InlineKeyboardButton(text="1K", callback_data="nano_res:1k"),
            InlineKeyboardButton(text="2K", callback_data="nano_res:2k"),
        ],
        [
            InlineKeyboardButton(text="9:16", callback_data="nano_rat:portrait_9_16"),
            InlineKeyboardButton(text="16:9", callback_data="nano_rat:landscape_16_9"),
            InlineKeyboardButton(text="1:1", callback_data="nano_rat:square_1_1"),
        ],
        [InlineKeyboardButton(text="\u25b6\ufe0f Generate", callback_data="nano_continue")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="back_to_menu")],
    ])
    return text, kb


def get_usage_history_message(today: int, month: int) -> str:
    return (
        "\U0001f4ca *Statistik Penggunaan*\n\n"
        f"Hari ini: {today} video\n"
        f"Bulan ini: {month} video\n"
    )
