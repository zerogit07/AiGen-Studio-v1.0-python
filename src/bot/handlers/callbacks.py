"""Callback query handlers for all inline keyboard actions."""
from __future__ import annotations

import asyncio
import logging
import random
import time

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from src.bot.menus.admin_ui import (
    get_admin_panel_keyboard,
    get_api_key_dashboard,
    get_backup_keyboard,
    get_broadcast_keyboard,
    get_key_list_keyboard,
    get_landing_page_keyboard,
    get_manage_keys_keyboard,
    get_manage_members_keyboard,
    get_manage_proxies_keyboard,
    get_member_dashboard,
    get_member_list_keyboard,
    get_payment_desc_keyboard,
    get_price_page_keyboard,
    get_proxy_dashboard,
    get_proxy_list_keyboard,
    get_stats_menu_keyboard,
)
from src.bot.menus.main import (
    get_kling21_config_keyboard,
    get_kling25_turbo_config_keyboard,
    get_kling26_motion_config_keyboard,
    get_kling26_pro_config_keyboard,
    get_main_menu_keyboard,
    get_nano_banana_config_keyboard,
    get_usage_history_message,
    get_veo31_config_keyboard,
)
from src.bot.panels.kling_v3_panel import get_kv3_state, kv3_state, render_kling_v3_panel
from src.bot.state import ADMIN_IDS, get_or_create_state, is_user_admin
from src.core.triple_pool import triple_pool
from src.database.apikeys import api_key_manager
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.proxies import proxy_manager
from src.database.settings import landing_page_manager
from src.database.usage import usage_manager
from src.database.users import user_manager
from src.services.jobs import finalize_job
from src.services.stats import global_logs, global_stats

logger = logging.getLogger(__name__)
router = Router(name="callbacks")

_user_last_command: dict[int, float] = {}


async def _safe_answer(callback: CallbackQuery, text: str = "") -> None:
    try:
        await callback.answer(text)
    except Exception:
        pass


@router.callback_query()
async def callback_handler(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user or not callback.message:
        await _safe_answer(callback)
        return

    user_id = user.id
    chat_id = callback.message.chat.id
    data = callback.data or ""

    now = time.time()
    if user_id in _user_last_command and now - _user_last_command[user_id] < 1.0:
        await _safe_answer(callback, "Terlalu cepat, tunggu sebentar.")
        return
    _user_last_command[user_id] = now

    state = await get_or_create_state(user_id, user.username or "", user.first_name or "", user.last_name or "")
    await _safe_answer(callback)

    # ─── Navigation ───
    if data == "noop":
        return

    if data == "close_panel":
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    if data == "back_to_menu":
        text = "\U0001f3ac Pilih model untuk generate:"
        try:
            await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        return

    if data == "back_to_banner":
        from src.bot.handlers.commands import handle_start_command
        try:
            await callback.message.delete()
        except Exception:
            pass
        await handle_start_command(callback.message, is_edit=False)
        return

    if data == "change_model":
        text = "\U0001f3ac Pilih model untuk generate:"
        try:
            await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        return

    # ─── Finish Again ───
    if data.startswith("finish_again:"):
        model_id = data.split(":")[1]
        state.model = model_id
        state.total_duration = 0
        state.current_shot_index = 0
        state.shots = []
        state.temp_prompt = None
        state.temp_image_url = None
        state.temp_image_url_last = None
        state.temp_video_url = None
        state.temp_image_refs = []

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        if model_id == "kling_2_5_turbo":
            state.resolution = "1080"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling25_turbo_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_6_pro":
            state.resolution = "1080"
            state.duration = "5"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling26_pro_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_2_6_motion" in model_id:
            state.orientation = "video"
            state.resolution = "720"
            state.step = "WAIT_ORIENTATION"
            msg, kb = get_kling26_motion_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_v3" in model_id:
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=model_id)
        elif "kling_o1" in model_id:
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model="kling_o1")
        elif "veo_3_1" in model_id:
            state.model = "veo_3_1_fast"
            state.resolution = "720"
            state.aspect_ratio = "portrait_9_16"
            state.duration = "8"
            state.step = "WAIT_MODEL_TYPE"
            msg, kb = get_veo31_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "nano_" in model_id:
            state.model = "nano_banana_flash"
            state.resolution = "1k"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_nano_banana_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        else:
            state.resolution = "720"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling21_config_keyboard(state)
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    # ─── Model Selection ───
    if data.startswith("model:"):
        model_id = data.split(":")[1]
        state.model = model_id
        state.temp_prompt = None
        state.temp_image_url = None
        state.temp_image_url_last = None
        state.temp_video_url = None
        state.temp_image_refs = []
        state.shots = []

        if model_id in ("kling_v3", "kling_v3_omni"):
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=model_id)
        elif model_id == "kling_o1":
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model="kling_o1")
        elif model_id == "nano_banana_flash":
            state.resolution = "1k"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_nano_banana_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "veo_3_1":
            state.model = "veo_3_1_fast"
            state.resolution = "720"
            state.aspect_ratio = "portrait_9_16"
            state.duration = "8"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_veo31_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_2_6_motion" in model_id:
            state.orientation = "video"
            state.resolution = "720"
            state.step = "WAIT_ORIENTATION"
            msg, kb = get_kling26_motion_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_6_pro":
            state.resolution = "1080"
            state.duration = "5"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling26_pro_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_5_turbo":
            state.resolution = "1080"
            state.duration = "5"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling25_turbo_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_v3_motion":
            state.orientation = "video"
            state.resolution = "720"
            state.step = "WAIT_ORIENTATION"
            msg, kb = get_kling26_motion_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        else:
            state.resolution = "720"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling21_config_keyboard(state)
            try:
                await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    # ─── Config Callbacks (Nano, Veo, Kling) ───
    if data.startswith("nano_mod:"):
        state.model = "nano_banana_pro" if data.split(":")[1] == "pro" else "nano_banana_flash"
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("nano_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("nano_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "nano_continue":
        state.step = "WAIT_PROMPT"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt teks Anda untuk generate gambar:")
        return

    if data.startswith("veo31_mod:"):
        state.model = "veo_3_1_standard" if data.split(":")[1] == "standard" else "veo_3_1_fast"
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_dur:"):
        state.duration = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_aud:"):
        state.generate_audio = data.split(":")[1] == "on"
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "veo31_continue":
        state.step = "WAIT_PROMPT"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt teks Anda untuk generate video:")
        return

    if data.startswith("k26m_ori:"):
        state.orientation = data.split(":")[1]
        msg, kb = get_kling26_motion_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k26m_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_kling26_motion_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "k26m_continue":
        state.step = "WAIT_PROMPT"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt dan gambar Anda untuk generate:")
        return

    if data.startswith("k21_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k21_dur:"):
        state.duration = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k21_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "k21_continue":
        state.step = "WAIT_PROMPT"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt teks Anda:")
        return

    if data.startswith("k26p_res:") or data.startswith("k25t_res:"):
        state.resolution = data.split(":")[1]
        if data.startswith("k26p"):
            msg, kb = get_kling26_pro_config_keyboard(state)
        else:
            msg, kb = get_kling25_turbo_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k26p_dur:") or data.startswith("k25t_dur:"):
        state.duration = data.split(":")[1]
        if data.startswith("k26p"):
            msg, kb = get_kling26_pro_config_keyboard(state)
        else:
            msg, kb = get_kling25_turbo_config_keyboard(state)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data in ("k26p_continue", "k25t_continue"):
        state.step = "WAIT_PROMPT"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt dan gambar Anda:")
        return

    # ─── Subscription / Payment ───
    if data in ("lite", "pro", "ultra"):
        state.temp_plan = data
        unique_code = random.randint(1, 999)
        state.temp_unique_code = unique_code

        key_map = {"lite": "priceLite", "pro": "pricePro", "ultra": "priceUltra"}
        base_price = int(landing_page_manager.get_setting(key_map[data]) or "0")
        total_price = base_price + unique_code
        formatted = f"{total_price:,}".replace(",", ".")

        desc_map = {"lite": "paymentDescriptionLite", "pro": "paymentDescriptionPro", "ultra": "paymentDescriptionUltra"}
        description = landing_page_manager.get_setting(desc_map[data])
        payment_image = landing_page_manager.get_setting("paymentImage")

        message_text = (
            f"*PEMBAYARAN PAKET {data.upper()}*\n\n"
            f"{description}\n\n"
            f"*PENTING:*\n"
            f"Silakan transfer sebesar:\n"
            f"*Rp {formatted}*\n\n"
            f"_(Mohon transfer tepat hingga 3 angka terakhir agar verifikasi otomatis lebih cepat)_\n\n"
            f"Silahkan scan QRIS diatas untuk pembayaran lalu kirim bukti pembayaran"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Kirim Bukti Transfer", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="Kembali", callback_data="back_to_banner")],
        ])

        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=payment_image, caption=message_text, parse_mode="Markdown"),
                reply_markup=keyboard,
            )
        except Exception:
            try:
                await callback.message.delete()
            except Exception:
                pass
            try:
                await bot.send_photo(chat_id=chat_id, photo=payment_image, caption=message_text, parse_mode="Markdown", reply_markup=keyboard)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown", reply_markup=keyboard)
        return

    if data == "confirm_payment":
        state.waiting_payment_proof = True
        await bot.send_message(chat_id=chat_id, text="\U0001f4f8 Silakan kirim bukti transfer (foto atau teks):")
        return

    if data == "free_trial":
        has_trial = await member_manager.has_used_trial(user_id)
        if has_trial:
            await bot.send_message(chat_id=chat_id, text="\u274c Anda sudah pernah menggunakan free trial.")
            return
        await member_manager.add_member(user_id, "testing", 7)
        await bot.send_message(
            chat_id=chat_id,
            text="\u2705 *Free Trial Aktif!*\n\nAnda mendapat 5 kuota trial selama 7 hari.\nKetik /menu untuk mulai generate.",
            parse_mode="Markdown",
        )
        return

    # ─── KV3 Panel Callbacks ───
    if data.startswith("kv3_"):
        await _handle_kv3_callback(callback, bot, user_id, chat_id, data, state)
        return

    # ─── Admin Panel ───
    if data == "admin_panel_back":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\u2699\ufe0f *Admin Panel*", parse_mode="Markdown", reply_markup=get_admin_panel_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\u2699\ufe0f *Admin Panel*", parse_mode="Markdown", reply_markup=get_admin_panel_keyboard())
        return

    if data == "admin_apikey":
        if not is_user_admin(user_id):
            return
        keys = api_key_manager.get_all_keys()
        now = int(time.time() * 1000)
        active = sum(1 for k in keys if k.active and k.cooldown_until < now)
        cooldown = sum(1 for k in keys if k.active and k.cooldown_until >= now)
        dead = sum(1 for k in keys if not k.active)
        msg, kb = get_api_key_dashboard(keys, active, cooldown, dead)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_key_btn":
        if not is_user_admin(user_id):
            return
        state.awaiting_api_key = True
        await bot.send_message(chat_id=chat_id, text="\U0001f5dd Kirimkan API key baru (satu per baris):")
        return

    if data == "list_key_btn":
        if not is_user_admin(user_id):
            return
        keys = api_key_manager.get_all_keys()
        msg, kb = get_key_list_keyboard(keys, page=1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data.startswith("kp:"):
        if not is_user_admin(user_id):
            return
        page = int(data.split(":")[1])
        keys = api_key_manager.get_all_keys()
        msg, kb = get_key_list_keyboard(keys, page=page)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "manage_keys":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f5dd *Manajemen Key*", parse_mode="Markdown", reply_markup=get_manage_keys_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f5dd *Manajemen Key*", parse_mode="Markdown", reply_markup=get_manage_keys_keyboard())
        return

    if data == "enable_all_keys":
        if not is_user_admin(user_id):
            return
        await api_key_manager.enable_all()
        triple_pool.rebuild()
        keys = api_key_manager.get_all_keys()
        msg, kb = get_api_key_dashboard(keys, len(keys), 0, 0)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f7e2 Semua key diaktifkan!")
        return

    if data == "disable_all_keys":
        if not is_user_admin(user_id):
            return
        await api_key_manager.disable_all()
        triple_pool.rebuild()
        keys = api_key_manager.get_all_keys()
        msg, kb = get_api_key_dashboard(keys, 0, 0, len(keys))
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f534 Semua key dinonaktifkan!")
        return

    if data == "delete_all_keys":
        if not is_user_admin(user_id):
            return
        await api_key_manager.delete_all()
        triple_pool.rebuild()
        keys = api_key_manager.get_all_keys()
        msg, kb = get_api_key_dashboard(keys, 0, 0, 0)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f5d1 Semua key dihapus!")
        return

    if data.startswith("t_key:"):
        if not is_user_admin(user_id):
            return
        key_prefix = data.split(":")[1]
        full_key = next((k.key for k in api_key_manager.get_all_keys() if k.key.startswith(key_prefix)), None)
        if full_key:
            await api_key_manager.toggle_key(full_key)
            triple_pool.rebuild()
        keys = api_key_manager.get_all_keys()
        msg, kb = get_key_list_keyboard(keys, page=state.current_page or 1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "check_key_btn":
        if not is_user_admin(user_id):
            return
        keys = api_key_manager.get_all_keys()
        if not keys:
            await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada key untuk dicek.")
            return
        await bot.send_message(chat_id=chat_id, text=f"\U0001f504 Mengecek {len(keys)} key...")
        valid = 0
        invalid = 0
        for k in keys:
            try:
                from src.services.request_engine import _request_once
                result = await _request_once("GET", f"https://api.freepik.com/v1/ai/text-to-image/nano-banana-pro-flash", k.key, "", None, None)
                if "error" not in result or result.get("status", 0) < 400:
                    valid += 1
                else:
                    invalid += 1
                    if result.get("error") == "dead_key":
                        await api_key_manager.mark_key_dead(k.key)
            except Exception:
                invalid += 1
        triple_pool.rebuild()
        await bot.send_message(chat_id=chat_id, text=f"\u2705 Selesai!\nValid: {valid}\nInvalid: {invalid}")
        return

    # ─── Proxy Admin ───
    if data == "admin_proxy":
        if not is_user_admin(user_id):
            return
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_dashboard(proxies)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_proxy_btn":
        if not is_user_admin(user_id):
            return
        state.waiting_proxy = True
        await bot.send_message(chat_id=chat_id, text="\U0001f310 Kirimkan proxy baru (satu per baris, format: http://user:pass@host:port):")
        return

    if data == "list_proxy_btn":
        if not is_user_admin(user_id):
            return
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_list_keyboard(proxies, page=1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data.startswith("pp:"):
        if not is_user_admin(user_id):
            return
        page = int(data.split(":")[1])
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_list_keyboard(proxies, page=page)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "manage_proxies":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f310 *Manajemen Proxy*", parse_mode="Markdown", reply_markup=get_manage_proxies_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f310 *Manajemen Proxy*", parse_mode="Markdown", reply_markup=get_manage_proxies_keyboard())
        return

    if data == "enable_all_proxies":
        if not is_user_admin(user_id):
            return
        await proxy_manager.enable_all()
        triple_pool.rebuild()
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_dashboard(proxies)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f7e2 Semua proxy diaktifkan!")
        return

    if data == "disable_all_proxies":
        if not is_user_admin(user_id):
            return
        await proxy_manager.disable_all()
        triple_pool.rebuild()
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_dashboard(proxies)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f534 Semua proxy dinonaktifkan!")
        return

    if data == "delete_all_proxies":
        if not is_user_admin(user_id):
            return
        await proxy_manager.delete_all()
        triple_pool.rebuild()
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_dashboard(proxies)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f5d1 Semua proxy dihapus!")
        return

    if data.startswith("t_proxy:"):
        if not is_user_admin(user_id):
            return
        proxy_prefix = data.split(":")[1]
        full_proxy = next((p.proxy for p in proxy_manager.get_all_proxies() if p.proxy.startswith(proxy_prefix)), None)
        if full_proxy:
            await proxy_manager.toggle_proxy(full_proxy)
            triple_pool.rebuild()
        proxies = proxy_manager.get_all_proxies()
        msg, kb = get_proxy_list_keyboard(proxies, page=state.current_page or 1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "check_proxy_btn":
        if not is_user_admin(user_id):
            return
        proxies = proxy_manager.get_all_proxies()
        if not proxies:
            await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada proxy untuk dicek.")
            return
        await bot.send_message(chat_id=chat_id, text=f"\U0001f504 Mengecek {len(proxies)} proxy...")
        result = await proxy_manager.check_all_proxies()
        triple_pool.rebuild()
        await bot.send_message(
            chat_id=chat_id,
            text=f"\u2705 Selesai!\nTotal: {result['total']}\nAktif: {result['active_count']}\nMati: {result['dead_count']}",
        )
        return

    # ─── Member Admin ───
    if data == "admin_member":
        if not is_user_admin(user_id):
            return
        members = member_manager.get_all_members()
        member_count = sum(1 for m in members.values() if m.plan in ("lite", "pro", "ultra"))
        trial_count = sum(1 for m in members.values() if m.plan == "testing")
        msg, kb = get_member_dashboard(members, member_count, trial_count)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_member_btn":
        if not is_user_admin(user_id):
            return
        state.waiting_add_member = True
        await bot.send_message(
            chat_id=chat_id,
            text="\u2795 Kirimkan data member baru:\n\nFormat: `user_id plan hari`\nContoh: `123456789 pro 30`",
            parse_mode="Markdown",
        )
        return

    if data == "list_member_btn":
        if not is_user_admin(user_id):
            return
        members = member_manager.get_all_members()
        members_list = list(members.items())
        msg, kb = get_member_list_keyboard(members_list, page=1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data.startswith("mp:"):
        if not is_user_admin(user_id):
            return
        page = int(data.split(":")[1])
        members = member_manager.get_all_members()
        members_list = list(members.items())
        msg, kb = get_member_list_keyboard(members_list, page=page)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "manage_members":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f465 *Manajemen Member*", parse_mode="Markdown", reply_markup=get_manage_members_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f465 *Manajemen Member*", parse_mode="Markdown", reply_markup=get_manage_members_keyboard())
        return

    if data == "enable_all_members":
        if not is_user_admin(user_id):
            return
        await member_manager.enable_all()
        members = member_manager.get_all_members()
        member_count = sum(1 for m in members.values() if m.plan in ("lite", "pro", "ultra"))
        trial_count = sum(1 for m in members.values() if m.plan == "testing")
        msg, kb = get_member_dashboard(members, member_count, trial_count)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f7e2 Semua member diaktifkan!")
        return

    if data == "disable_all_members":
        if not is_user_admin(user_id):
            return
        await member_manager.disable_all()
        members = member_manager.get_all_members()
        member_count = sum(1 for m in members.values() if m.plan in ("lite", "pro", "ultra"))
        trial_count = sum(1 for m in members.values() if m.plan == "testing")
        msg, kb = get_member_dashboard(members, member_count, trial_count)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f534 Semua member dinonaktifkan!")
        return

    if data == "delete_all_members":
        if not is_user_admin(user_id):
            return
        await member_manager.delete_all()
        members = member_manager.get_all_members()
        msg, kb = get_member_dashboard(members, 0, 0)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f5d1 Semua member dihapus!")
        return

    if data == "remove_member_btn":
        if not is_user_admin(user_id):
            return
        state.waiting_check_user = False
        state.step = "WAIT_REMOVE_MEMBER"
        await bot.send_message(chat_id=chat_id, text="\U0001f5d1 Kirimkan User ID member yang ingin dihapus:")
        return

    if data.startswith("v_mem:"):
        if not is_user_admin(user_id):
            return
        target_uid = data.split(":")[1]
        member = member_manager.get_member_data(int(target_uid))
        user_data = await user_manager.get_user_data(int(target_uid))
        info = f"*Info Member `{target_uid}`*\n\n"
        if user_data:
            info += f"Username: {user_data.get('username', '-')}\n"
            info += f"Nama: {user_data.get('full_name', '-')}\n"
        if member:
            info += f"Plan: {member.plan}\nAktif: {member.active}\nExpired: {member.expire_date or '-'}\n"
            info += f"Sisa Hari: {member.remaining_days}\n"
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="list_member_btn")]])
        try:
            await callback.message.edit_text(text=info, parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=info, parse_mode="Markdown", reply_markup=back_kb)
        return

    if data.startswith("t_mem:"):
        if not is_user_admin(user_id):
            return
        target_uid = data.split(":")[1]
        member = member_manager.get_member_data(int(target_uid))
        if member:
            member.active = not member.active
            from src.database.db import get_db
            db = await get_db()
            await db.execute("UPDATE members SET active=? WHERE user_id=?", (int(member.active), target_uid))
            await db.commit()
        members = member_manager.get_all_members()
        members_list = list(members.items())
        msg, kb = get_member_list_keyboard(members_list, page=state.current_page or 1)
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    # ─── Broadcast ───
    if data == "admin_broadcast":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f4e2 *Broadcast*\n\nPilih target:", parse_mode="Markdown", reply_markup=get_broadcast_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f4e2 *Broadcast*", parse_mode="Markdown", reply_markup=get_broadcast_keyboard())
        return

    if data.startswith("broadcast_"):
        if not is_user_admin(user_id):
            return
        target = data.replace("broadcast_", "")
        state.waiting_broadcast = True
        state.broadcast_target = target
        await bot.send_message(chat_id=chat_id, text=f"\U0001f4e2 Kirimkan pesan broadcast untuk {target}:")
        return

    # ─── Stats ───
    if data == "admin_stats":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f4ca *Statistik*", parse_mode="Markdown", reply_markup=get_stats_menu_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f4ca *Statistik*", parse_mode="Markdown", reply_markup=get_stats_menu_keyboard())
        return

    if data == "admin_stats_full":
        if not is_user_admin(user_id):
            return
        usage_today = usage_manager.get_total_usage_today()
        usage_month = usage_manager.get_total_usage_month()
        msg = get_usage_history_message(usage_today, usage_month)
        msg += f"\n\n*Global Stats:*\n- Total video: {global_stats.total_videos}\n"
        for m_id, count in global_stats.model_usage.items():
            msg += f"  - {m_id}: {count}\n"
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_stats")]])
        try:
            await callback.message.edit_text(text=msg, parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=back_kb)
        return

    if data == "admin_stats_trial":
        if not is_user_admin(user_id):
            return
        trial_users = member_manager.get_members_by_plan("testing")
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_stats")]])
        if not trial_users:
            try:
                await callback.message.edit_text(text="\U0001f4cb Tidak ada user trial.", reply_markup=back_kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text="\U0001f4cb Tidak ada user trial.", reply_markup=back_kb)
            return
        lines = ["*Daftar User Trial:*\n"]
        for uid in trial_users:
            m = member_manager.get_member_data(int(uid))
            quota = m.testing_quota if m else 0
            lines.append(f"- `{uid}` | Quota: {quota}")
        try:
            await callback.message.edit_text(text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        return

    if data == "admin_stats_member":
        if not is_user_admin(user_id):
            return
        members = member_manager.get_all_members()
        paid_members = {uid: m for uid, m in members.items() if m.plan in ("lite", "pro", "ultra")}
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_stats")]])
        if not paid_members:
            try:
                await callback.message.edit_text(text="\U0001f4cb Tidak ada member berbayar.", reply_markup=back_kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text="\U0001f4cb Tidak ada member berbayar.", reply_markup=back_kb)
            return
        lines = ["*Daftar Member Berbayar:*\n"]
        for uid, m in paid_members.items():
            status = "\U0001f7e2" if m.active and not m.is_expired else "\U0001f534"
            lines.append(f"- `{uid}` | {m.plan} | {status} | Exp: {m.expire_date or '-'}")
        text = "\n".join(lines)
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await bot.send_message(chat_id=chat_id, text=text[i:i + 4000], parse_mode="Markdown")
        else:
            try:
                await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=back_kb)
            except Exception:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=back_kb)
        return

    if data == "admin_check_user":
        if not is_user_admin(user_id):
            return
        state.waiting_check_user = True
        await bot.send_message(chat_id=chat_id, text="\U0001f50d Kirimkan User ID yang ingin dicek:")
        return

    # ─── Backup ───
    if data == "admin_backup":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f4be *Backup*", parse_mode="Markdown", reply_markup=get_backup_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f4be *Backup*", parse_mode="Markdown", reply_markup=get_backup_keyboard())
        return

    if data == "admin_backup_members":
        if not is_user_admin(user_id):
            return
        members = member_manager.get_all_members()
        if not members:
            await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada data member.")
            return
        lines = ["*Backup Data Member:*\n"]
        for uid, m in members.items():
            lines.append(f"- `{uid}` | {m.plan} | Active: {m.active} | Exp: {m.expire_date or '-'}")
        text = "\n".join(lines)
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await bot.send_message(chat_id=chat_id, text=text[i:i + 4000], parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        return

    if data == "admin_backup_keys":
        if not is_user_admin(user_id):
            return
        keys = api_key_manager.get_all_keys()
        if not keys:
            await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada data API key.")
            return
        lines = ["*Backup Data API Key:*\n"]
        for i, k in enumerate(keys, 1):
            status = "\U0001f7e2" if k.active else "\U0001f534"
            lines.append(f"{i}. `{k.key}` {status}")
        text = "\n".join(lines)
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await bot.send_message(chat_id=chat_id, text=text[i:i + 4000], parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        return

    if data == "admin_backup_proxies":
        if not is_user_admin(user_id):
            return
        proxies = proxy_manager.get_all_proxies()
        if not proxies:
            await bot.send_message(chat_id=chat_id, text="\u274c Tidak ada data proxy.")
            return
        lines = ["*Backup Data Proxy:*\n"]
        for i, p in enumerate(proxies, 1):
            status = "\U0001f7e2" if p.active else "\U0001f534"
            lines.append(f"{i}. `{p.proxy}` {status}")
        text = "\n".join(lines)
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await bot.send_message(chat_id=chat_id, text=text[i:i + 4000], parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        return

    # ─── Landing Page ───
    if data == "admin_landing_page":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f3e0 *Landing Page*", parse_mode="Markdown", reply_markup=get_landing_page_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f3e0 *Landing Page*", parse_mode="Markdown", reply_markup=get_landing_page_keyboard())
        return

    if data == "edit_lp_banner_img":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_banner_img = True
        await bot.send_message(chat_id=chat_id, text="\U0001f5bc Kirimkan URL gambar banner baru:")
        return

    if data == "edit_lp_banner_desc":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_banner_desc = True
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan deskripsi banner baru:")
        return

    if data == "edit_lp_pay_img":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_pay_img = True
        await bot.send_message(chat_id=chat_id, text="\U0001f4b3 Kirimkan URL gambar QRIS/payment baru:")
        return

    if data == "edit_lp_pay_desc":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f4dd *Edit Deskripsi Payment*", parse_mode="Markdown", reply_markup=get_payment_desc_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f4dd *Edit Deskripsi Payment*", parse_mode="Markdown", reply_markup=get_payment_desc_keyboard())
        return

    if data == "edit_lp_pay_desc_lite":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_pay_desc_lite = True
        await bot.send_message(chat_id=chat_id, text="\U0001f331 Kirimkan deskripsi pembayaran Lite baru:")
        return

    if data == "edit_lp_pay_desc_pro":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_pay_desc_pro = True
        await bot.send_message(chat_id=chat_id, text="\u2b50 Kirimkan deskripsi pembayaran Pro baru:")
        return

    if data == "edit_lp_pay_desc_ultra":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_pay_desc_ultra = True
        await bot.send_message(chat_id=chat_id, text="\U0001f48e Kirimkan deskripsi pembayaran Ultra baru:")
        return

    if data == "edit_lp_prices":
        if not is_user_admin(user_id):
            return
        try:
            await callback.message.edit_text(text="\U0001f4b0 *Edit Harga*", parse_mode="Markdown", reply_markup=get_price_page_keyboard())
        except Exception:
            await bot.send_message(chat_id=chat_id, text="\U0001f4b0 *Edit Harga*", parse_mode="Markdown", reply_markup=get_price_page_keyboard())
        return

    if data == "edit_lp_price_lite":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_price_lite = True
        await bot.send_message(chat_id=chat_id, text="\U0001f331 Kirimkan harga Lite baru (angka saja):")
        return

    if data == "edit_lp_price_pro":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_price_pro = True
        await bot.send_message(chat_id=chat_id, text="\u2b50 Kirimkan harga Pro baru (angka saja):")
        return

    if data == "edit_lp_price_ultra":
        if not is_user_admin(user_id):
            return
        state.waiting_lp_price_ultra = True
        await bot.send_message(chat_id=chat_id, text="\U0001f48e Kirimkan harga Ultra baru (angka saja):")
        return

    # ─── Maintenance ───
    if data == "admin_maintenance":
        if not is_user_admin(user_id):
            return
        is_maint = model_manager.is_maintenance()
        text = f"\u2699\ufe0f *Maintenance Mode*\n\nStatus: {'ON \U0001f534' if is_maint else 'OFF \U0001f7e2'}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Toggle ON/OFF", callback_data="toggle_maintenance")],
            [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
        ])
        try:
            await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "toggle_maintenance":
        if not is_user_admin(user_id):
            return
        is_maint = model_manager.is_maintenance()
        await model_manager.set_maintenance(not is_maint)
        new_status = "ON \U0001f534" if not is_maint else "OFF \U0001f7e2"
        text = f"\u2699\ufe0f *Maintenance Mode*\n\nStatus: {new_status}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Toggle ON/OFF", callback_data="toggle_maintenance")],
            [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
        ])
        try:
            await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=kb)
        return


async def _handle_kv3_callback(
    callback: CallbackQuery, bot: Bot, user_id: int, chat_id: int, data: str, state: any
) -> None:
    """Handle all kv3_ prefixed callbacks for the Kling V3 panel."""
    kv3 = get_kv3_state(user_id)

    if data == "kv3_edit_prompt":
        kv3.awaiting_input = "prompt"
        await bot.send_message(chat_id=chat_id, text="\U0001f4dd Kirimkan prompt baru:")
        return

    if data == "kv3_upload_first_frame":
        kv3.awaiting_input = "first_frame"
        await bot.send_message(chat_id=chat_id, text="\U0001f5bc Kirimkan gambar untuk First Frame:")
        return

    if data == "kv3_upload_end_frame":
        kv3.awaiting_input = "end_frame"
        await bot.send_message(chat_id=chat_id, text="\U0001f5bc Kirimkan gambar untuk End Frame:")
        return

    if data == "kv3_upload_element":
        kv3.awaiting_input = "element"
        await bot.send_message(chat_id=chat_id, text=f"\U0001f5bc Kirimkan gambar element ({len(kv3.element_urls)}/3):")
        return

    if data == "kv3_change_duration":
        kv3.panel_view = "choose_main_duration"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_change_resolution":
        kv3.panel_view = "choose_resolution"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_change_ratio":
        kv3.panel_view = "choose_ratio"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_toggle_audio":
        kv3.audio = not kv3.audio
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_multishot_on":
        kv3.multi_shot_on = True
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_multishot_off":
        kv3.multi_shot_on = False
        kv3.shots.clear()
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_add_shot":
        kv3.awaiting_input = "shot_prompt"
        await bot.send_message(chat_id=chat_id, text=f"\U0001f4dd Kirimkan prompt untuk Shot {len(kv3.shots) + 1}:")
        return

    if data == "kv3_close_subpanel":
        kv3.panel_view = "main"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data.startswith("kv3_set_main_dur_"):
        dur = data.replace("kv3_set_main_dur_", "")
        kv3.duration = f"{dur}s"
        kv3.panel_view = "main"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data.startswith("kv3_set_res_"):
        kv3.resolution = data.replace("kv3_set_res_", "")
        kv3.panel_view = "main"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data.startswith("kv3_set_ratio_"):
        kv3.ratio = data.replace("kv3_set_ratio_", "")
        kv3.panel_view = "main"
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=True, force_model=kv3.model_type)
        return

    if data == "kv3_generate":
        if not kv3.prompt:
            await bot.send_message(chat_id=chat_id, text="\u274c Prompt belum diisi!")
            return

        member_data = await member_manager.sync_member(user_id)
        if not member_data:
            await bot.send_message(chat_id=chat_id, text="\u274c Anda belum terdaftar sebagai member.")
            return
        if member_data.is_expired and member_data.plan != "testing":
            await bot.send_message(chat_id=chat_id, text="\u274c Membership Anda sudah expired.")
            return
        if not member_data.active:
            await bot.send_message(chat_id=chat_id, text="\u274c Akun Anda dinonaktifkan.")
            return

        usage_data = await usage_manager.get_usage(user_id)
        daily_limit = member_manager.get_daily_limit(member_data.plan, user_id)
        if usage_data.video_today >= daily_limit:
            await bot.send_message(chat_id=chat_id, text=f"\u274c Kuota harian habis ({usage_data.video_today}/{daily_limit}).")
            return
        if member_data.plan == "testing" and member_data.testing_quota <= 0:
            await bot.send_message(chat_id=chat_id, text="\u274c Kuota trial Anda sudah habis.")
            return

        can_start = await member_manager.start_process(user_id, member_data.plan)
        if not can_start:
            await bot.send_message(chat_id=chat_id, text="\u274c Proses penuh. Tunggu proses sebelumnya selesai.")
            return

        if model_manager.is_maintenance():
            await bot.send_message(chat_id=chat_id, text="\u274c Bot sedang dalam mode maintenance.")
            await member_manager.end_process(user_id)
            return

        status_msg = await bot.send_message(chat_id=chat_id, text="\u23f3 Memproses permintaan Anda...")

        dur_num = int(kv3.duration.replace("s", "")) if kv3.duration else 5
        state_data = {
            "duration": str(dur_num),
            "resolution": kv3.resolution.replace("p", ""),
            "aspect_ratio": kv3.ratio,
            "temp_image_url": kv3.first_frame_url,
            "temp_image_url_last": kv3.end_frame_url,
            "temp_image_refs": kv3.element_urls,
            "generate_audio": kv3.audio,
            "shots": kv3.shots,
            "kling3_mode": "multi_intelligence" if kv3.multi_shot_on else None,
        }

        asyncio.create_task(finalize_job(
            bot=bot,
            user_id=user_id,
            chat_id=chat_id,
            prompt=kv3.prompt,
            model_id=kv3.model_type,
            state_data=state_data,
            status_msg_id=status_msg.message_id,
        ))
        return
