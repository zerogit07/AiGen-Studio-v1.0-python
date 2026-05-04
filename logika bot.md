# Logika Bot AiGen Studio v1.0

## Tech Stack
- **aiogram** — Telegram Bot framework (async, polling mode)
- **aiosqlite** — Local SQLite database (async)
- **aiohttp** — HTTP client untuk Freepik AI API
- **python-dotenv** — Environment configuration
- **redis** — Caching & state store (optional)
- **asyncio.create_task()** — Background job processing

## Arsitektur

```
main.py                    # Entry point + bot initialization
├── src/
│   ├── core/
│   │   ├── types.py       # Dataclasses (UserState, MemberData, ApiKey, etc.)
│   │   ├── constants.py   # Model configs, fingerprints, default settings
│   │   └── triple_pool.py # API Key + Proxy + Fingerprint rotation
│   ├── database/
│   │   ├── db.py          # SQLite connection + schema init
│   │   ├── members.py     # MemberManager (CRUD, quota, expiry)
│   │   ├── apikeys.py     # ApiKeyManager (rotation, cooldown)
│   │   ├── proxies.py     # ProxyManager (health check, rotation)
│   │   ├── usage.py       # UsageManager (daily/monthly counters)
│   │   ├── users.py       # UserManager (track all users)
│   │   ├── settings.py    # LandingPageManager (LP settings)
│   │   └── models.py      # ModelManager (maintenance mode)
│   ├── bot/
│   │   ├── state.py       # User state management + admin IDs
│   │   ├── handlers/
│   │   │   ├── commands.py   # /start, /admin, /menu
│   │   │   ├── callbacks.py  # All inline keyboard actions
│   │   │   └── messages.py   # Text input + photo upload handlers
│   │   ├── menus/
│   │   │   ├── main.py       # Main menu + model config keyboards
│   │   │   └── admin_ui.py   # Admin panel keyboards
│   │   └── panels/
│   │       └── kling_v3_panel.py  # Kling V3/Omni/O1 advanced panel
│   └── services/
│       ├── request_engine.py  # aiohttp request engine + key rotation
│       ├── freepik_api.py     # Freepik AI API router
│       ├── polling.py         # Job status polling (10s interval)
│       ├── jobs.py            # Job orchestration (submit + poll)
│       └── stats.py           # Global activity logging
├── data/bot.db               # SQLite database file
└── logs/bot.log              # Application logs
```

## Alur Utama

### 1. Startup
1. `main.py` load `.env`, init logging
2. Connect SQLite database (`data/bot.db`), create tables if not exist
3. Load all data: members, API keys, proxies, users, settings, model status
4. Build TriplePool (API key + proxy + fingerprint combinations)
5. Start state cleaner background task (cleanup idle states setiap 5 menit)
6. Set bot commands, start polling

### 2. User Flow - Generate Video/Image
```
/start → Landing Page (non-member) ATAU Main Menu (member)
   ↓
Pilih Model → Config Panel (durasi, resolusi, aspect ratio)
   ↓
Kirim Prompt (text/image) → Validasi:
   ├── Member aktif?
   ├── Quota harian?
   ├── Trial quota?
   ├── Maintenance mode?
   └── Max concurrent process?
   ↓
asyncio.create_task(finalize_job()) → Background:
   ├── Acquire TripleSet (API key + proxy + fingerprint)
   ├── Submit ke Freepik API
   ├── Release TripleSet (tidak di-hold selama polling)
   ├── Poll status setiap 10 detik (max 180 = 30 menit)
   ├── On complete: kirim video/image + increment usage
   └── On fail/timeout: kirim error message
```

### 3. Admin Flow
```
/admin → Admin Panel:
   ├── API Key: tambah, list, toggle, enable/disable all, delete all, check validity
   ├── Proxy: tambah, list, toggle, enable/disable all, delete all, check connectivity
   ├── Member: tambah, list, toggle, remove, enable/disable all, delete all
   ├── Broadcast: ke semua user, member saja, atau trial saja
   ├── Stats: full stats, trial users, paid members, check user
   ├── Backup: export data member/key/proxy
   ├── Landing Page: edit banner, payment images, descriptions, prices
   └── Maintenance: toggle mode maintenance
```

### 4. Payment Flow
```
User klik paket (Lite/Pro/Ultra) → Tampil QRIS + harga + kode unik
   ↓
User klik "Kirim Bukti Transfer" → Bot minta foto/teks bukti
   ↓
Bukti dikirim ke semua admin → Admin verifikasi manual
   ↓
Admin tambah member via admin panel → User jadi member aktif
```

### 5. Free Trial
```
User klik "Free Trial" → Cek apakah sudah pernah trial
   ├── Sudah pernah → Tolak
   └── Belum → Buat member "testing" (5 quota, 7 hari)
```

## Database Schema (SQLite)

### members
| Column | Type | Description |
|---|---|---|
| user_id | TEXT PK | Telegram user ID |
| plan | TEXT | lite/pro/ultra/testing |
| expired | TEXT | ISO date string |
| testing_quota | INT | Remaining trial quota |
| active | INT | 0/1 |
| current_process | INT | Active job count |
| created_at | TEXT | ISO timestamp |

### api_keys
| Column | Type | Description |
|---|---|---|
| key | TEXT PK | Freepik API key |
| active | INT | 0/1 |
| cooldown_until | INT | Epoch ms cooldown |

### proxies
| Column | Type | Description |
|---|---|---|
| proxy | TEXT PK | Proxy URL |
| active | INT | 0/1 |
| cooldown_until | INT | Epoch ms cooldown |

### usage
| Column | Type | Description |
|---|---|---|
| user_id | TEXT PK | Telegram user ID |
| video_today | INT | Daily counter |
| last_reset | TEXT | Date string |
| video_month | INT | Monthly counter |
| last_month_reset | TEXT | Month string |

### users, jobs, models_status, settings
See `src/database/db.py` for full schema.

## Model Support (25+ models)
- **Kling V3**: Pro, Std, Motion Pro/Std, Omni Pro/Std
- **Kling 2.6**: Pro, Motion Pro/Std
- **Kling 2.5**: Turbo
- **Kling 2.1**: Pro, Std
- **Kling O1**: Pro, Std
- **Veo 3.1**: Standard, Fast, Ingredient
- **Nano Banana**: Flash, Pro

## Fitur Keamanan
- Admin check pada semua admin callbacks
- Rate limiting 2 detik antar command
- State cleaner otomatis (30 menit idle)
- Error message sanitization (tidak expose internal details)
- TriplePool release setelah submit (cegah deadlock selama polling)
- Broadcast rate limiting (25 msg/detik)
- Free trial abuse prevention (cek history)

## Key Differences dari Versi Lama
| Aspek | Lama | Baru |
|---|---|---|
| Bot Framework | python-telegram-bot 21.5 | aiogram 3.15 |
| Database | Supabase (cloud PostgreSQL) | aiosqlite (local SQLite) |
| HTTP Client | httpx | aiohttp |
| Job Queue | arq (Redis worker) | asyncio.create_task() |
| Web Server | FastAPI + uvicorn | Tidak ada (bot only) |
| Entry Point | server.py + worker.py | main.py saja |
