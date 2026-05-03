# Logika Bot AiGen Studio v1.0

## Arsitektur Sistem

```
┌────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Telegram Bot   │────▶│   FastAPI     │────▶│   Supabase    │
│  (Polling Mode) │     │   (Port 3000) │     │   (Database)  │
└───────┬────────┘     └──────────────┘     └───────────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│  Redis Queue    │────▶│   Worker      │
│  (arq)          │     │  (worker.py)  │
└────────────────┘     └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  Freepik AI  │
                       │  API         │
                       └──────────────┘
```

### Komponen Utama

| Komponen | File | Fungsi |
|---|---|---|
| Server | `server.py` | FastAPI + Telegram bot lifecycle, health endpoint |
| Worker | `worker.py` | Background job processor (generate video/image, cek key) |
| Queue | `src/core/queue.py` | Redis job queue via arq |
| Triple Pool | `src/core/triple_pool.py` | Rotasi API key + proxy + fingerprint |
| Request Engine | `src/services/request_engine.py` | HTTP client resilient dengan retry & rotasi |

---

## Alur Utama Bot

### 1. Startup (server.py)

```
1. Load .env.local dan .env
2. Buat FastAPI app dengan lifespan context manager
3. Inisialisasi Telegram Bot (python-telegram-bot)
   - Set timeout: connect=20s, read=20s, write=20s, pool=20s
   - Polling read timeout: 30s
4. Register handlers: /start, /admin, callback, photo, text
5. post_init():
   a. Load semua data dari Supabase secara paralel:
      - API keys, members, custom limits, model status
      - proxies, landing page settings, usage, users
   b. Set bot commands (/start, /admin)
   c. Start state cleaner background task
   d. Cek semua proxy (startup health check)
6. Start polling mode
```

### 2. Alur User Baru (/start)

```
User kirim /start
  │
  ▼
Cek membership via member_manager.sync_member()
  │
  ├── Bukan member ──▶ Tampilkan halaman landing (banner + harga)
  │                      │
  │                      ├── Klik "Free Trial" ──▶ Cek belum pernah trial ──▶ Daftar testing 30 hari
  │                      ├── Klik "Lite/Pro/Ultra" ──▶ Tampilkan payment page
  │                      │     └── Kirim bukti transfer ──▶ Notify admin
  │                      └── Klik "Kembali" ──▶ Menu utama
  │
  └── Sudah member ──▶ Tampilkan menu utama (pilih model)
                         │
                         ├── Pilih model ──▶ Set state.model ──▶ Tampilkan config model
                         │     │
                         │     ├── Set durasi, resolusi, ratio, dll
                         │     └── Klik "Generate" ──▶ WAIT_PROMPT
                         │
                         └── Klik "Profil" ──▶ Tampilkan info membership & usage
```

### 3. Alur Generate (Prompt → Hasil)

```
User kirim prompt (text/photo)
  │
  ▼
Validasi:
  ├── Cek member aktif? (not expired, active=true)
  ├── Cek kuota harian? (usage_today < daily_limit)
  ├── Cek kuota trial? (testing_quota > 0)
  ├── Cek maintenance mode?
  └── Cek max concurrent process?
  │
  ▼ (semua OK)
add_job() ──▶ Redis queue (arq)
  │
  ▼
Worker process_generation():
  1. Acquire triple_set (API key + proxy + fingerprint)
  2. finalize_job():
     a. Download image jika ada (base64 encode)
     b. Buat GenerateParams
     c. submit_video_generation() via request_engine
     d. Release triple_set (SETELAH submit, SEBELUM polling)
     e. watch_generation() polling status setiap 10 detik (max 30 menit)
  3. Status completed ──▶ Kirim video/photo ke user, increment_usage()
  4. Status failed ──▶ Kirim pesan error ke user
  5. Timeout ──▶ Kirim pesan timeout ke user
```

### 4. Request Engine (Rotasi Key & Proxy)

```
request_engine() dipanggil
  │
  ▼
Ada triple_set? ──▶ Pakai langsung (key + proxy + fingerprint dari pool)
  │
  └── Tidak ada ──▶ Rotasi manual:
      1. Ambil key yang di-force (jika ada)
      2. Ambil rotated keys (round-robin)
      3. Untuk setiap key:
         a. Coba dengan 3 proxy berbeda
         b. Jika gagal semua proxy, coba direct (tanpa proxy)
         c. Handle status code:
            - 200: Sukses
            - 400: Bad request (raise langsung)
            - 401: Key invalid → mark_key_dead()
            - 403/429: Rate limit → raise RequestEngineHTTPError
            - 500/503: Server error → set_cooldown proxy, retry
      4. Semua gagal → raise RuntimeError
```

### 5. Triple Pool

```
TripleSet = API Key + Proxy + Fingerprint

acquire():
  1. Cari triple yang available (not in_use, not burned, cooldown selesai)
  2. Jika tidak ada, tunggu (asyncio.sleep loop)
  3. Mark in_use = True
  4. Return triple_set

release():
  1. Mark in_use = False
  2. Set last_used = now

mark_burned():
  1. Set burned = True
  2. Set cooldown 30 menit

refresh():
  1. Buat kombinasi dari semua active keys × active proxies
  2. Generate fingerprint unik per kombinasi
```

---

## Sistem Membership

### Tier & Kuota

| Plan | Daily Limit | Max Concurrent | Durasi |
|---|---|---|---|
| testing | 3 (dari testing_quota) | 1 | 30 hari |
| lite | 20 (configurable) | 2 | Sesuai pembelian |
| pro | 50 (configurable) | 3 | Sesuai pembelian |
| ultra | 999 (configurable) | 5 | Sesuai pembelian |

### Alur Membership

```
1. Pendaftaran:
   - Free Trial: 1x per user, 30 hari, 3 kuota
   - Berbayar: User pilih plan → transfer → kirim bukti → admin verifikasi

2. Validasi (setiap generate):
   - Cek active == true
   - Cek expire_date > now
   - Cek video_today < daily_limit
   - Cek current_process < max_process

3. Usage tracking:
   - video_today: Reset otomatis setiap hari baru (UTC)
   - video_month: Reset otomatis setiap bulan baru
   - Increment setelah job COMPLETED (bukan saat submit)
```

---

## Admin Panel

### Menu Admin (/admin)

```
Admin Panel
├── Manajemen API Key
│   ├── Dashboard (aktif/cooldown/mati)
│   ├── Tambah Key
│   ├── Cek Semua Key
│   ├── Lihat Daftar (paginated)
│   └── Manajemen (enable_all / disable_all / delete_all)
│
├── Manajemen Proxy
│   ├── Dashboard (aktif/mati)
│   ├── Tambah Proxy
│   ├── Cek Semua Proxy
│   ├── Lihat Daftar (paginated)
│   └── Manajemen (enable_all / disable_all / delete_all)
│
├── Manajemen Model
│   ├── Toggle Model (on/off per model)
│   └── Toggle Maintenance Mode
│
├── Manajemen Member
│   ├── Dashboard (paid/trial counts)
│   ├── Tambah Member
│   ├── Lihat Member (paginated)
│   ├── Hapus Member
│   └── Manajemen (enable_all / disable_all / delete_all)
│
├── Landing Page
│   ├── Halaman Awal (banner image & desc)
│   ├── Halaman Payment (payment image & desc per plan)
│   └── Manajemen Harga (harga per plan)
│
├── Manajemen Limit
│   ├── Limit Lite
│   ├── Limit Pro
│   └── Limit Ultra
│
├── Manajemen Pesan
│   ├── Broadcast Global / Member / Trial
│   └── Chat Personal
│
├── Backup
│   ├── Backup Member / Key / Proxy / Semua
│
├── Statistik
│   ├── User Trial / Member
│   ├── Log Aktivitas
│   ├── Cek Akun
│   └── Statistik Lengkap
│
└── Logout
```

### Admin Authentication

```
1. User kirim /admin
2. Cek user_id ada di ADMIN_IDS (env variable, comma-separated)
3. Jika admin → set state.is_admin = True, tampilkan panel
4. Semua callback admin di-guard dengan is_user_admin()
5. Logout: set state.is_admin = False
```

---

## Database (Supabase)

### Tabel

| Tabel | Fungsi | Primary Key |
|---|---|---|
| members | Data membership user | user_id |
| api_keys | API key Freepik | key |
| proxies | Daftar proxy | proxy |
| jobs | Log job generate | job_id |
| usage | Tracking penggunaan harian/bulanan | user_id |
| users | Data user Telegram | user_id |
| models_status | Status on/off per model | id |
| settings | Konfigurasi (maintenance, limits, landing page) | id |

### Async Wrapper

```
Supabase Python SDK bersifat synchronous.
AsyncSupabaseClient membungkus semua .execute() dengan asyncio.to_thread()
agar tidak blocking event loop Telegram bot.

Alur:
  supabase.table("x").select("*").eq("col", val).execute()
  └── AsyncSupabaseQueryBuilder chains method calls
      └── .execute() → asyncio.to_thread(sync_builder.execute)
```

---

## State Management

### UserState (In-Memory)

```
Setiap user punya UserState di dict global (src/bot/state.py)
- Dibuat saat user pertama kali kirim pesan
- Otomatis dihapus setelah 30 menit tidak aktif (state cleaner)
- Menyimpan:
  - Model yang dipilih
  - Konfigurasi generate (durasi, resolusi, ratio)
  - Step saat ini (WAIT_PROMPT, WAIT_REMOVE_MEMBER, dll)
  - Flag admin, flag waiting_* untuk input flows
  - Temporary data (prompt, image url, payment code)
```

### Flow Control via state.step

```
state.step = None          → Idle, tunggu user pilih menu
state.step = "WAIT_PROMPT" → Tunggu user kirim prompt teks/foto
state.step = "WAIT_REMOVE_MEMBER" → Tunggu admin kirim user ID untuk dihapus
```

### Flow Control via state.waiting_*

```
state.awaiting_api_key = True    → Tunggu admin kirim API key
state.waiting_proxy = True       → Tunggu admin kirim proxy
state.waiting_add_member = True  → Tunggu admin kirim user_id plan hari
state.waiting_broadcast = True   → Tunggu admin kirim teks broadcast
state.waiting_payment_proof = True → Tunggu user kirim bukti bayar
state.waiting_lp_* = True        → Tunggu admin kirim konten landing page
```

---

## Worker (Background Jobs)

### Arsitektur

```
Redis Queue (arq) ──▶ Worker Process (worker.py)

Worker Functions:
1. process_generation    → Generate video/image via Freepik API
2. process_check_single_key → Cek health 1 API key
3. process_check_batch_timeout → Handle timeout batch key check

Config:
- max_jobs: 5 (concurrent)
- max_tries: 1 (no retry)
- job_timeout: 1 jam
```

### Batch Key Checking

```
Admin klik "Cek Semua" di API Key panel
  │
  ▼
1. init_key_check_batch() → Set counter di Redis
2. Enqueue process_check_single_key per key (parallel)
3. Enqueue process_check_batch_timeout (defer 5 menit)
4. Setiap key selesai dicek → simpan hasil di Redis hash
5. Jika semua selesai ATAU timeout:
   → send_batch_report() ke admin
   → Cleanup Redis keys
```

---

## Model Support

### Model Video
- Kling v3 (Std/Pro/Omni)
- Kling 2.1
- Kling 2.5 Turbo
- Kling 2.6 Pro / Motion
- Veo 3.1 (Google)
- Wan (Alibaba)
- Runway Gen-4
- MiniMax (Hailuo)
- SkyReels V2

### Model Image
- Nano Banana (nano2 / pro)

### Konfigurasi Per Model (constants.py)

```python
MODEL_CONFIG = {
    "model_id": ModelConfig(
        endpoint="video/endpoint-path",
        status_path="video/status-path",
        needs_duration=True/False,
        durations=["5", "10"],
        needs_orientation=True/False,
        resolution="720"/"1080",
    )
}
```

---

## Keamanan

### Proteksi Admin
- Semua callback admin di-guard dengan `is_user_admin(user_id, state)`
- Admin IDs dari environment variable (ADMIN_IDS)
- Admin bisa logout (state.is_admin = False)

### Rate Limiting
- User: Cooldown 2 detik antar pesan
- Broadcast: 25 pesan per detik (delay 1s setiap 25 pesan)
- Member sync: Max 1 sync per 60 detik per user

### API Key Protection
- Key di-mask di log (hanya 8 char pertama)
- Key di-mask di UI admin (12 char pertama)
- Backup menampilkan full key (hanya untuk admin)

### Error Handling
- Error internal di-log ke file, user hanya lihat pesan generic
- Tidak ada informasi teknis (status code, stack trace) yang dikirim ke user
- Semua DB operations di-wrap try/except
