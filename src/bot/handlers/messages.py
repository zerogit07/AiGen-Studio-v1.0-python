"""Message handlers — text input, photo uploads, broadcast."""
from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, F, Router
from aiogram.types import Message

from src.bot.panels.kling_v3_panel import get_kv3_state, render_kling_v3_panel
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

logger = logging.getLogger(__name__)
router = Router(name="messages")

_user_last_command: dict[int, float] = {}


@router.message(F.text)
async def text_handler(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user or not message.text:
        return

    user_id = user.id
    chat_id = message.chat.id
    text = message.text.strip()

    now = time.time()
    if user_id in _user_last_command and now - _user_last_command[user_id] < 2.0:
        return
    _user_last_command[user_id] = now

    state = await get_or_create_state(user_id, user.username or "", user.first_name or "", user.last_name or "")

    # KV3 panel text input
    kv3 = get_kv3_state(user_id)
    if kv3.awaiting_input == "prompt":
        kv3.prompt = text
        kv3.awaiting_input = None
        await message.reply("Prompt diterima!")
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
        return

    if kv3.awaiting_input == "shot_prompt":
        dur = int(kv3.duration.replace("s", "")) if kv3.duration else 5
        kv3.shots.append({"prompt": text, "duration": dur})
        kv3.awaiting_input = None
        await message.reply(f"Shot {len(kv3.shots)} diterima!")
        await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
        return

    # API Key input (admin)
    if state.awaiting_api_key:
        state.awaiting_api_key = False
        if not is_user_admin(user_id):
            return
        keys_added = 0
        for line in text.split("\n"):
            line = line.strip()
            if line:
                await api_key_manager.add_key(line)
                keys_added += 1
        triple_pool.rebuild()
        await message.reply(f"\u2705 {keys_added} API key ditambahkan.")
        return

    # Proxy input (admin)
    if state.waiting_proxy:
        state.waiting_proxy = False
        if not is_user_admin(user_id):
            return
        proxies_added = 0
        for line in text.split("\n"):
            line = line.strip()
            if line:
                await proxy_manager.add_proxy(line)
                proxies_added += 1
        triple_pool.rebuild()
        await message.reply(f"\u2705 {proxies_added} proxy ditambahkan.")
        return

    # Add member (admin)
    if state.waiting_add_member:
        state.waiting_add_member = False
        if not is_user_admin(user_id):
            return
        parts = text.split()
        if len(parts) < 3:
            await message.reply("Format salah. Gunakan: `user_id plan hari`", parse_mode="Markdown")
            return
        try:
            target_uid = int(parts[0])
            plan = parts[1].lower()
            days = int(parts[2])
        except ValueError:
            await message.reply("Format salah. Contoh: `123456789 pro 30`", parse_mode="Markdown")
            return
        if plan not in ("lite", "pro", "ultra", "testing"):
            await message.reply("Plan harus lite, pro, ultra, atau testing.")
            return
        await member_manager.add_member(target_uid, plan, days)
        await message.reply(f"\u2705 Member `{target_uid}` ditambahkan ({plan}, {days} hari).", parse_mode="Markdown")
        return

    # Broadcast (admin)
    if state.waiting_broadcast:
        state.waiting_broadcast = False
        if not is_user_admin(user_id):
            return
        target = state.broadcast_target or "all"
        state.broadcast_target = None

        users_to_send: list[int] = []
        if target == "all":
            users_to_send = user_manager.get_all_users()
        elif target == "member":
            users_to_send = [
                int(uid) for uid, m in member_manager.get_all_members().items()
                if m.plan in ("lite", "pro", "ultra")
            ]
        elif target == "trial":
            users_to_send = [int(uid) for uid in member_manager.get_members_by_plan("testing")]

        sent = 0
        failed = 0
        await message.reply(f"Mengirim broadcast ke {len(users_to_send)} user...")
        for i, uid in enumerate(users_to_send):
            try:
                await bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
                sent += 1
            except Exception:
                failed += 1
            if (i + 1) % 25 == 0:
                await asyncio.sleep(1.0)
        await message.reply(f"*Broadcast Selesai*\n- Terkirim: {sent}\n- Gagal: {failed}", parse_mode="Markdown")
        return

    # Check user (admin)
    if state.waiting_check_user:
        state.waiting_check_user = False
        try:
            target_uid = int(text)
        except ValueError:
            await message.reply("User ID harus angka.")
            return
        member = member_manager.get_member_data(target_uid)
        user_data = await user_manager.get_user_data(target_uid)
        if not member and not user_data:
            await message.reply(f"User `{target_uid}` tidak ditemukan.", parse_mode="Markdown")
            return
        info = f"*Info User `{target_uid}`*\n\n"
        if user_data:
            info += f"Username: {user_data.get('username', '-')}\nNama: {user_data.get('full_name', '-')}\n"
        if member:
            info += f"Plan: {member.plan}\nAktif: {member.active}\nExpired: {member.expire_date or '-'}\n"
        await message.reply(info, parse_mode="Markdown")
        return

    # Payment proof (text)
    if state.waiting_payment_proof:
        state.waiting_payment_proof = False
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"*BUKTI PEMBAYARAN BARU*\n\n"
                        f"User: `{user_id}`\nPlan: {state.temp_plan}\n"
                        f"Kode Unik: {state.temp_unique_code}\n\nPesan: {text}"
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        await message.reply("*Bukti pembayaran diterima!*\n\nAdmin akan memverifikasi.", parse_mode="Markdown")
        return

    # Remove member (admin)
    if state.step == "WAIT_REMOVE_MEMBER":
        state.step = None
        target_id = text.strip()
        try:
            await member_manager.remove_member(target_id)
            await message.reply(f"Member `{target_id}` berhasil dihapus.", parse_mode="Markdown")
        except Exception as exc:
            logger.error("Error removing member %s: %s", target_id, exc)
            await message.reply("Gagal menghapus member. Coba lagi.")
        return

    # LP settings handlers (admin)
    lp_handlers = [
        ("waiting_lp_banner_img", "bannerImage"),
        ("waiting_lp_banner_desc", "bannerDescription"),
        ("waiting_lp_pay_img", "paymentImage"),
        ("waiting_lp_pay_desc_lite", "paymentDescriptionLite"),
        ("waiting_lp_pay_desc_pro", "paymentDescriptionPro"),
        ("waiting_lp_pay_desc_ultra", "paymentDescriptionUltra"),
        ("waiting_lp_price_lite", "priceLite"),
        ("waiting_lp_price_pro", "pricePro"),
        ("waiting_lp_price_ultra", "priceUltra"),
    ]
    for attr, setting_key in lp_handlers:
        if getattr(state, attr, False):
            setattr(state, attr, False)
            if not is_user_admin(user_id):
                return
            await landing_page_manager.update_setting(setting_key, text)
            await message.reply(f"\u2705 {setting_key} diperbarui.")
            return

    # Prompt input (generate)
    if state.step == "WAIT_PROMPT" and state.model:
        member_data = await member_manager.sync_member(user_id)
        if not member_data:
            await message.reply("Anda belum terdaftar sebagai member. Silakan daftar terlebih dahulu.")
            state.step = None
            return
        if member_data.is_expired and member_data.plan != "testing":
            await message.reply("Membership Anda sudah expired. Silakan perpanjang.")
            state.step = None
            return
        if not member_data.active:
            await message.reply("Akun Anda sedang dinonaktifkan. Hubungi admin.")
            state.step = None
            return
        usage_data = await usage_manager.get_usage(user_id)
        daily_limit = member_manager.get_daily_limit(member_data.plan, user_id)
        if usage_data.video_today >= daily_limit:
            await message.reply(f"Kuota harian habis ({usage_data.video_today}/{daily_limit}). Coba lagi besok.")
            state.step = None
            return
        if member_data.plan == "testing" and member_data.testing_quota <= 0:
            await message.reply("Kuota trial Anda sudah habis.")
            state.step = None
            return
        if model_manager.is_maintenance():
            await message.reply("Bot sedang dalam mode maintenance. Coba lagi nanti.")
            state.step = None
            return

        can_start = await member_manager.start_process(user_id, member_data.plan)
        if not can_start:
            await message.reply("Proses penuh. Tunggu proses sebelumnya selesai.")
            state.step = None
            return

        state.temp_prompt = text
        state.step = None

        status_msg = await message.reply("\u23f3 Memproses permintaan Anda...")

        state_data = {
            "duration": state.duration,
            "aspect_ratio": state.aspect_ratio,
            "orientation": state.orientation,
            "resolution": state.resolution,
            "temp_image_url": state.temp_image_url,
            "temp_image_url_last": state.temp_image_url_last,
            "temp_image_refs": list(state.temp_image_refs),
            "temp_video_url": state.temp_video_url,
            "generate_audio": state.generate_audio,
            "shots": [{"prompt": s.prompt, "duration": s.duration} for s in state.shots],
            "kling3_mode": state.kling3_mode,
            "camera_config": state.camera_config,
        }

        asyncio.create_task(finalize_job(
            bot=bot,
            user_id=user_id,
            chat_id=chat_id,
            prompt=text,
            model_id=state.model,
            state_data=state_data,
            status_msg_id=status_msg.message_id,
        ))
        return


@router.message(F.photo)
async def photo_handler(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user or not message.photo:
        return

    user_id = user.id
    chat_id = message.chat.id

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_url = file.file_path

    # KV3 panel image upload
    kv3 = get_kv3_state(user_id)
    if kv3.awaiting_input:
        if kv3.awaiting_input == "first_frame":
            kv3.first_frame_url = file_url
            kv3.awaiting_input = None
            await message.reply("First Frame diterima!")
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return
        elif kv3.awaiting_input == "end_frame":
            kv3.end_frame_url = file_url
            kv3.awaiting_input = None
            await message.reply("End Frame diterima!")
            await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return
        elif kv3.awaiting_input == "element":
            if len(kv3.element_urls) < 3:
                kv3.element_urls.append(file_url)
                await message.reply(f"Element {len(kv3.element_urls)}/3 diterima!")
                if len(kv3.element_urls) >= 3:
                    kv3.awaiting_input = None
                    await render_kling_v3_panel(bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return

    state = await get_or_create_state(user_id, user.username or "", user.first_name or "", user.last_name or "")

    # Payment proof as photo
    if state.waiting_payment_proof:
        state.waiting_payment_proof = False
        caption = message.caption or ""
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=(
                        f"*BUKTI PEMBAYARAN BARU*\n\n"
                        f"User: `{user_id}`\nPlan: {state.temp_plan}\n"
                        f"Kode Unik: {state.temp_unique_code}\n"
                        f"Keterangan: {caption}"
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        await message.reply("*Bukti pembayaran diterima!*\n\nAdmin akan memverifikasi.", parse_mode="Markdown")
        return

    # Image for generate (prompt with image)
    if state.step == "WAIT_PROMPT" and state.model:
        state.temp_image_url = file_url
        caption = message.caption or ""
        if caption:
            state.temp_prompt = caption
            state.step = None

            can_start = await member_manager.start_process(user_id, (await member_manager.sync_member(user_id) or type("", (), {"plan": "testing"})).plan)
            if not can_start:
                await message.reply("Proses penuh. Tunggu proses sebelumnya selesai.")
                return

            status_msg = await message.reply("\u23f3 Memproses permintaan Anda...")
            state_data = {
                "duration": state.duration,
                "aspect_ratio": state.aspect_ratio,
                "orientation": state.orientation,
                "resolution": state.resolution,
                "temp_image_url": state.temp_image_url,
                "temp_image_url_last": state.temp_image_url_last,
                "temp_image_refs": list(state.temp_image_refs),
                "generate_audio": state.generate_audio,
                "shots": [{"prompt": s.prompt, "duration": s.duration} for s in state.shots],
                "kling3_mode": state.kling3_mode,
                "camera_config": state.camera_config,
            }
            asyncio.create_task(finalize_job(
                bot=bot,
                user_id=user_id,
                chat_id=chat_id,
                prompt=caption,
                model_id=state.model,
                state_data=state_data,
                status_msg_id=status_msg.message_id,
            ))
        else:
            await message.reply("\U0001f5bc Gambar diterima! Sekarang kirimkan prompt teks Anda:")
        return
