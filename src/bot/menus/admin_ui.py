from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import ProxyEntry


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Manajemen API Key", callback_data="api_mgmt_menu"),
            InlineKeyboardButton("Manajemen Proxy", callback_data="admin_proxy"),
        ],
        [
            InlineKeyboardButton("Manajemen Model", callback_data="admin_model"),
            InlineKeyboardButton("Manajemen Member", callback_data="admin_member"),
        ],
        [
            InlineKeyboardButton("Landing Page", callback_data="admin_landing_page"),
            InlineKeyboardButton("Manajemen Limit", callback_data="admin_lp_limits"),
        ],
        [
            InlineKeyboardButton("Manajemen Pesan", callback_data="admin_msg_mgmt"),
            InlineKeyboardButton("Manajemen Backup", callback_data="admin_backup_mgmt"),
        ],
        [
            InlineKeyboardButton("Logout", callback_data="admin_logout"),
            InlineKeyboardButton("Statistik", callback_data="admin_stats"),
        ],
    ])


def get_backup_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Backup Data Member", callback_data="admin_backup_members")],
        [InlineKeyboardButton("Backup Data API Key", callback_data="admin_backup_keys")],
        [InlineKeyboardButton("Backup Data Proxy", callback_data="admin_backup_proxies")],
        [InlineKeyboardButton("Backup Semua Data", callback_data="admin_backup")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel")],
    ])


def get_message_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Broadcast Global", callback_data="admin_broadcast_all")],
        [InlineKeyboardButton("Broadcast Member", callback_data="admin_broadcast_member")],
        [InlineKeyboardButton("Broadcast Trial", callback_data="admin_broadcast_trial")],
        [InlineKeyboardButton("Chat Personal", callback_data="admin_chat_personal")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])


def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Daftar User Trial", callback_data="admin_stats_trial")],
        [InlineKeyboardButton("Daftar User Member", callback_data="admin_stats_member")],
        [InlineKeyboardButton("Log Aktivitas Terbaru", callback_data="admin_stats_logs")],
        [InlineKeyboardButton("Cek Akun", callback_data="admin_stats_check_user")],
        [InlineKeyboardButton("Statistik Bot Lengkap", callback_data="admin_stats_full")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])


def get_landing_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Halaman Awal", callback_data="admin_lp_home")],
        [InlineKeyboardButton("Halaman Payment", callback_data="admin_lp_payment")],
        [InlineKeyboardButton("Manajemen Harga", callback_data="admin_lp_prices")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])


def get_limit_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Limit Lite", callback_data="edit_limit_lite")],
        [InlineKeyboardButton("Limit Pro", callback_data="edit_limit_pro")],
        [InlineKeyboardButton("Limit Ultra", callback_data="edit_limit_ultra")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])


def get_home_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Gambar Banner", callback_data="edit_lp_banner_img")],
        [InlineKeyboardButton("Deskripsi Banner", callback_data="edit_lp_banner_desc")],
        [InlineKeyboardButton("Kembali", callback_data="admin_landing_page")],
    ])


def get_payment_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Gambar Payment", callback_data="edit_lp_pay_img")],
        [InlineKeyboardButton("Deskripsi AiGen Lite", callback_data="edit_lp_pay_desc_lite")],
        [InlineKeyboardButton("Deskripsi AiGen Pro", callback_data="edit_lp_pay_desc_pro")],
        [InlineKeyboardButton("Deskripsi AiGen Ultra", callback_data="edit_lp_pay_desc_ultra")],
        [InlineKeyboardButton("Kembali", callback_data="admin_landing_page")],
    ])


def get_price_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Harga Lite", callback_data="edit_lp_price_lite")],
        [InlineKeyboardButton("Harga Pro", callback_data="edit_lp_price_pro")],
        [InlineKeyboardButton("Harga Ultra", callback_data="edit_lp_price_ultra")],
        [InlineKeyboardButton("Kembali", callback_data="admin_landing_page")],
    ])


def get_proxy_dashboard(all_proxies: list[ProxyEntry]) -> tuple[str, InlineKeyboardMarkup]:
    active_count = sum(1 for p in all_proxies if p.active)
    message = (
        f"*Manajemen Proxy*\n\n"
        f"*Statistik:*\n"
        f"- Total Proxy: {len(all_proxies)}\n"
        f"- Aktif: {active_count}\n"
        f"- Mati/Nonaktif: {len(all_proxies) - active_count}\n\n"
        f"Pilih menu di bawah untuk mengelola proxy."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Tambah Proxy", callback_data="add_proxy_btn"),
            InlineKeyboardButton("Cek Semua", callback_data="check_proxy_btn"),
        ],
        [
            InlineKeyboardButton("Lihat Daftar", callback_data="list_proxy_btn"),
            InlineKeyboardButton("Manajemen", callback_data="manage_proxies"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_proxies_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Aktifkan Semua", callback_data="enable_all_proxies")],
        [InlineKeyboardButton("Nonaktifkan Semua", callback_data="disable_all_proxies")],
        [InlineKeyboardButton("Hapus Semua", callback_data="delete_all_proxies")],
        [InlineKeyboardButton("Kembali", callback_data="admin_proxy")],
    ])


def get_member_dashboard(members: dict, member_count: int, trial_count: int) -> tuple[str, InlineKeyboardMarkup]:
    message = (
        f"*Manajemen Member*\n\n"
        f"*Statistik:*\n"
        f"- Total Member: {member_count}\n"
        f"- Trial: {trial_count}\n\n"
        f"Pilih menu di bawah:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Tambah Member", callback_data="add_member_btn")],
        [InlineKeyboardButton("Lihat Member", callback_data="list_member_btn")],
        [InlineKeyboardButton("Hapus Member", callback_data="remove_member_btn")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_members_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Kembali", callback_data="admin_member")],
    ])


def get_model_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Toggle Model", callback_data="toggle_model_btn")],
        [InlineKeyboardButton("Toggle Maintenance", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])


def get_manage_models_keyboard(models: list[dict]) -> tuple[str, InlineKeyboardMarkup]:
    lines = ["*Status Model:*\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for m in models:
        status_icon = "ON" if m["active"] else "OFF"
        lines.append(f"- {m['name']}: {status_icon}")
        buttons.append([
            InlineKeyboardButton(
                f"{'OFF' if m['active'] else 'ON'} {m['name']}",
                callback_data=f"toggle_model:{m['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton("Kembali", callback_data="admin_model")])
    return "\n".join(lines), InlineKeyboardMarkup(buttons)


def get_api_key_dashboard(keys: list, active_count: int, cooldown_count: int, dead_count: int) -> tuple[str, InlineKeyboardMarkup]:
    message = (
        f"*Manajemen API Key*\n\n"
        f"*Statistik:*\n"
        f"- Total Key: {len(keys)}\n"
        f"- Aktif: {active_count}\n"
        f"- Cooldown: {cooldown_count}\n"
        f"- Mati: {dead_count}\n\n"
        f"Pilih menu di bawah:"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Tambah Key", callback_data="add_key_btn"),
            InlineKeyboardButton("Cek Semua", callback_data="test_keys_btn"),
        ],
        [
            InlineKeyboardButton("Lihat Daftar", callback_data="list_keys_btn"),
            InlineKeyboardButton("Manajemen", callback_data="manage_keys"),
        ],
        [InlineKeyboardButton("Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_keys_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Aktifkan Semua", callback_data="enable_all_keys")],
        [InlineKeyboardButton("Kembali", callback_data="api_mgmt_menu")],
    ])


def get_manage_categorized_keys_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Kembali", callback_data="api_mgmt_menu")],
    ])


def get_usage_history_message(usage_today: int, usage_month: int) -> str:
    return (
        f"*Statistik Penggunaan*\n\n"
        f"- Hari ini: {usage_today} video\n"
        f"- Bulan ini: {usage_month} video"
    )
