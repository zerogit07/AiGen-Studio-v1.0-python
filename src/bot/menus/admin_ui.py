"""Admin panel menus and keyboards."""
from __future__ import annotations

import math
import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import ApiKey, MemberData, ProxyEntry


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f5dd API Key", callback_data="admin_apikey"),
            InlineKeyboardButton(text="\U0001f310 Proxy", callback_data="admin_proxy"),
        ],
        [
            InlineKeyboardButton(text="\U0001f465 Member", callback_data="admin_member"),
            InlineKeyboardButton(text="\U0001f4e2 Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton(text="\U0001f4ca Stats", callback_data="admin_stats"),
            InlineKeyboardButton(text="\U0001f4be Backup", callback_data="admin_backup"),
        ],
        [
            InlineKeyboardButton(text="\U0001f3e0 Landing Page", callback_data="admin_landing_page"),
            InlineKeyboardButton(text="\u2699\ufe0f Maintenance", callback_data="admin_maintenance"),
        ],
        [InlineKeyboardButton(text="\u274c Tutup", callback_data="close_panel")],
    ])


def get_api_key_dashboard(
    keys: list[ApiKey], active: int, cooldown: int, dead: int
) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "\U0001f5dd *Manajemen API Key*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Total Key: {len(keys)}\n"
        f"- Aktif: \U0001f7e2 {active}\n"
        f"- Cooldown: \U0001f7e1 {cooldown}\n"
        f"- Mati: \U0001f534 {dead}\n\n"
        "Pilih menu di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u2795 Tambah Key", callback_data="add_key_btn"),
            InlineKeyboardButton(text="\U0001f504 Cek Semua", callback_data="check_key_btn"),
        ],
        [
            InlineKeyboardButton(text="\U0001f4cb Lihat Daftar", callback_data="list_key_btn"),
            InlineKeyboardButton(text="\U0001f510 Manajemen", callback_data="manage_keys"),
        ],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return text, kb


def get_manage_keys_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Aktifkan Semua", callback_data="enable_all_keys")],
        [InlineKeyboardButton(text="\U0001f534 Nonaktifkan Semua", callback_data="disable_all_keys")],
        [InlineKeyboardButton(text="\U0001f5d1 Hapus Semua", callback_data="delete_all_keys")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_apikey")],
    ])


def get_key_list_keyboard(keys: list[ApiKey], page: int = 1, per_page: int = 10) -> tuple[str, InlineKeyboardMarkup]:
    total = len(keys)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_keys = keys[start:start + per_page]

    now = int(time.time() * 1000)
    text = f"\U0001f5dd *Daftar API Key (Halaman {page}/{total_pages})*\n\n"
    rows: list[list[InlineKeyboardButton]] = []
    for i, k in enumerate(page_keys, start + 1):
        if not k.active:
            icon = "\U0001f534"
        elif k.cooldown_until >= now:
            icon = "\U0001f7e1"
        else:
            icon = "\U0001f7e2"
        short = k.key[:10] + "..."
        rows.append([
            InlineKeyboardButton(text=f"{icon} {short}", callback_data=f"v_key:{k.key[:20]}"),
            InlineKeyboardButton(text="\U0001f504", callback_data=f"t_key:{k.key[:20]}"),
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="\u25c0\ufe0f", callback_data=f"kp:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="\u25b6\ufe0f", callback_data=f"kp:{page + 1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_apikey")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def get_proxy_dashboard(all_proxies: list[ProxyEntry]) -> tuple[str, InlineKeyboardMarkup]:
    active_count = sum(1 for p in all_proxies if p.active)
    text = (
        "\U0001f310 *Manajemen Proxy*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Total Proxy: {len(all_proxies)}\n"
        f"- Aktif: \U0001f7e2 {active_count}\n"
        f"- Mati/Nonaktif: \U0001f534 {len(all_proxies) - active_count}\n\n"
        "Pilih menu di bawah untuk mengelola proxy."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u2795 Tambah Proxy", callback_data="add_proxy_btn"),
            InlineKeyboardButton(text="\U0001f504 Cek Semua", callback_data="check_proxy_btn"),
        ],
        [
            InlineKeyboardButton(text="\U0001f4cb Lihat Daftar", callback_data="list_proxy_btn"),
            InlineKeyboardButton(text="\U0001f510 Manajemen", callback_data="manage_proxies"),
        ],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return text, kb


def get_manage_proxies_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Aktifkan Semua", callback_data="enable_all_proxies")],
        [InlineKeyboardButton(text="\U0001f534 Nonaktifkan Semua", callback_data="disable_all_proxies")],
        [InlineKeyboardButton(text="\U0001f5d1 Hapus Semua", callback_data="delete_all_proxies")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_proxy")],
    ])


def get_proxy_list_keyboard(proxies: list[ProxyEntry], page: int = 1, per_page: int = 10) -> tuple[str, InlineKeyboardMarkup]:
    total = len(proxies)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_proxies = proxies[start:start + per_page]

    text = f"\U0001f310 *Daftar Proxy (Halaman {page}/{total_pages})*\n\n"
    rows: list[list[InlineKeyboardButton]] = []
    for p in page_proxies:
        icon = "\U0001f7e2" if p.active else "\U0001f534"
        short = p.proxy[:25] + "..." if len(p.proxy) > 25 else p.proxy
        rows.append([
            InlineKeyboardButton(text=f"{icon} {short}", callback_data=f"v_proxy:{p.proxy[:30]}"),
            InlineKeyboardButton(text="\U0001f504", callback_data=f"t_proxy:{p.proxy[:30]}"),
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="\u25c0\ufe0f", callback_data=f"pp:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="\u25b6\ufe0f", callback_data=f"pp:{page + 1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_proxy")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def get_member_dashboard(members: dict, member_count: int, trial_count: int) -> tuple[str, InlineKeyboardMarkup]:
    lite_count = sum(1 for m in members.values() if m.plan.lower() == "lite")
    pro_count = sum(1 for m in members.values() if m.plan.lower() == "pro")
    ultra_count = sum(1 for m in members.values() if m.plan.lower() == "ultra")

    text = (
        "\U0001f465 *Manajemen Member*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Lite: {lite_count}\n"
        f"- Pro: {pro_count}\n"
        f"- Ultra: {ultra_count}\n"
        f"- Trial: {trial_count}\n"
        f"- Total: {len(members)}\n\n"
        "Pilih menu di bawah:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u2795 Tambah Member", callback_data="add_member_btn"),
            InlineKeyboardButton(text="\U0001f4cb Lihat Member", callback_data="list_member_btn"),
        ],
        [
            InlineKeyboardButton(text="\U0001f5d1 Hapus Member", callback_data="remove_member_btn"),
            InlineKeyboardButton(text="\U0001f510 Manajemen", callback_data="manage_members"),
        ],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return text, kb


def get_manage_members_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Aktifkan Semua", callback_data="enable_all_members")],
        [InlineKeyboardButton(text="\U0001f534 Nonaktifkan Semua", callback_data="disable_all_members")],
        [InlineKeyboardButton(text="\U0001f5d1 Hapus Semua", callback_data="delete_all_members")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_member")],
    ])


def get_member_list_keyboard(members_list: list, page: int = 1, per_page: int = 15) -> tuple[str, InlineKeyboardMarkup]:
    total = len(members_list)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_items = members_list[start:start + per_page]

    text = f"\U0001f465 *Daftar Member (Halaman {page}/{total_pages})*\n\n"
    rows: list[list[InlineKeyboardButton]] = []
    for uid, m in page_items:
        uid_str = str(uid)
        icon = "\U0001f7e2" if m.active else "\U0001f534"
        uid_short = uid_str[:8] + ".." if len(uid_str) > 8 else uid_str
        rows.append([
            InlineKeyboardButton(text=f"\U0001f464 {uid_short}", callback_data=f"v_mem:{uid_str}"),
            InlineKeyboardButton(text="\U0001f441\ufe0f", callback_data=f"v_mem:{uid_str}"),
            InlineKeyboardButton(text=icon, callback_data=f"t_mem:{uid_str}"),
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="\u25c0\ufe0f", callback_data=f"mp:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="\u25b6\ufe0f", callback_data=f"mp:{page + 1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_member")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4e2 Semua User", callback_data="broadcast_all")],
        [InlineKeyboardButton(text="\U0001f465 Member Saja", callback_data="broadcast_member")],
        [InlineKeyboardButton(text="\U0001f9ea Trial Saja", callback_data="broadcast_trial")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca Full Stats", callback_data="admin_stats_full")],
        [InlineKeyboardButton(text="\U0001f9ea Trial Users", callback_data="admin_stats_trial")],
        [InlineKeyboardButton(text="\U0001f465 Member List", callback_data="admin_stats_member")],
        [InlineKeyboardButton(text="\U0001f50d Check User", callback_data="admin_check_user")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_backup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f465 Backup Member", callback_data="admin_backup_members")],
        [InlineKeyboardButton(text="\U0001f5dd Backup Key", callback_data="admin_backup_keys")],
        [InlineKeyboardButton(text="\U0001f310 Backup Proxy", callback_data="admin_backup_proxies")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_landing_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f5bc Banner Image", callback_data="edit_lp_banner_img")],
        [InlineKeyboardButton(text="\U0001f4dd Banner Desc", callback_data="edit_lp_banner_desc")],
        [InlineKeyboardButton(text="\U0001f4b3 Payment Image", callback_data="edit_lp_pay_img")],
        [InlineKeyboardButton(text="\U0001f4dd Payment Desc", callback_data="edit_lp_pay_desc")],
        [InlineKeyboardButton(text="\U0001f4b0 Harga/Limit", callback_data="edit_lp_prices")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_payment_desc_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f331 Deskripsi AiGen Lite", callback_data="edit_lp_pay_desc_lite")],
        [InlineKeyboardButton(text="\u2b50 Deskripsi AiGen Pro", callback_data="edit_lp_pay_desc_pro")],
        [InlineKeyboardButton(text="\U0001f48e Deskripsi AiGen Ultra", callback_data="edit_lp_pay_desc_ultra")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_landing_page")],
    ])


def get_price_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f331 Harga Lite", callback_data="edit_lp_price_lite")],
        [InlineKeyboardButton(text="\u2b50 Harga Pro", callback_data="edit_lp_price_pro")],
        [InlineKeyboardButton(text="\U0001f48e Harga Ultra", callback_data="edit_lp_price_ultra")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Kembali", callback_data="admin_landing_page")],
    ])
