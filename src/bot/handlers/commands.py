"""Command handlers — /start, /admin, /menu."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from src.bot.menus.admin_ui import get_admin_panel_keyboard
from src.bot.menus.main import get_main_menu_keyboard
from src.bot.state import get_or_create_state, is_user_admin
from src.database.members import member_manager
from src.database.settings import landing_page_manager

logger = logging.getLogger(__name__)
router = Router(name="commands")


async def handle_start_command(message: Message, is_edit: bool = False) -> None:
    user = message.from_user
    if not user:
        return
    user_id = user.id
    chat_id = message.chat.id

    state = await get_or_create_state(user_id, user.username or "", user.first_name or "", user.last_name or "")
    member_data = await member_manager.sync_member(user_id)

    if member_data and member_data.active and not member_data.is_expired:
        text = (
            f"Halo, *{user.first_name or 'User'}*! \U0001f44b\n\n"
            "\U0001f3ac Selamat datang di *AiGen Studio*.\n"
            "Pilih model di bawah untuk mulai generate:"
        )
        kb = get_main_menu_keyboard()
        if is_edit:
            try:
                await message.edit_text(text=text, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await message.answer(text=text, parse_mode="Markdown", reply_markup=kb)
        else:
            await message.answer(text=text, parse_mode="Markdown", reply_markup=kb)
        return

    banner_img = landing_page_manager.get_setting("bannerImage")
    banner_desc = landing_page_manager.get_setting("bannerDescription")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f331 Lite", callback_data="lite"),
         InlineKeyboardButton(text="\u2b50 Pro", callback_data="pro"),
         InlineKeyboardButton(text="\U0001f48e Ultra", callback_data="ultra")],
        [InlineKeyboardButton(text="\U0001f9ea Free Trial", callback_data="free_trial")],
    ])

    try:
        await message.answer_photo(photo=banner_img, caption=banner_desc, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await message.answer(text=banner_desc, parse_mode="Markdown", reply_markup=kb)


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    await handle_start_command(message, is_edit=False)


@router.message(Command("admin"))
async def admin_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    if not is_user_admin(user.id):
        await message.answer("Anda bukan admin.")
        return
    await message.answer(
        "\u2699\ufe0f *Admin Panel*",
        parse_mode="Markdown",
        reply_markup=get_admin_panel_keyboard(),
    )


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    member_data = await member_manager.sync_member(user.id)
    if not member_data or not member_data.active or member_data.is_expired:
        await message.answer("Anda belum terdaftar atau membership expired. Ketik /start untuk info.")
        return
    await message.answer(
        "\U0001f3ac Pilih model untuk generate:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )
