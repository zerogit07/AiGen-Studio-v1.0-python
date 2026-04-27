from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import UserState


def get_main_keyboard(active_models: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(active_models), 2):
        row_models = active_models[i : i + 2]
        row = [
            InlineKeyboardButton(
                f"      {m['name']}      ", callback_data=f"model:{m['id']}"
            )
            for m in row_models
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def get_resolution_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("720p", callback_data="resolution:720"),
            InlineKeyboardButton("1080p", callback_data="resolution:1080"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_orientation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Video (Max 30s)", callback_data="orientation:video"),
            InlineKeyboardButton("Image (Max 10s)", callback_data="orientation:image"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_o1_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Mode Interpolasi", callback_data="o1_mode:interpolation"),
            InlineKeyboardButton("Mode Reference", callback_data="o1_mode:reference"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_audio_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Audio On", callback_data="audio:on"),
            InlineKeyboardButton("Audio Off", callback_data="audio:off"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_use_image_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ya (Gunakan Gambar)", callback_data="use_image:yes"),
            InlineKeyboardButton("Tidak (Teks Saja)", callback_data="use_image:no"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_kling3_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Tanpa Multi-shot", callback_data="kling3_mode:single"),
            InlineKeyboardButton("Multi-shot Auto", callback_data="kling3_mode:multi_intelligence"),
        ],
        [InlineKeyboardButton("Multi-shot Custom", callback_data="kling3_mode:multi_customize")],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_veo_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("T2V (Text to Video)", callback_data="veo_mode:t2v")],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])


def get_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("16:9 (Widescreen)", callback_data="ratio:widescreen_16_9"),
            InlineKeyboardButton("9:16 (Portrait)", callback_data="ratio:portrait_9_16"),
        ],
        [InlineKeyboardButton("1:1 (Square)", callback_data="ratio:square_1_1")],
        [InlineKeyboardButton("Kembali", callback_data="back_main")],
    ])
