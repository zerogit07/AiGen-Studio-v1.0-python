"""SQLite database initialization and connection management."""
from __future__ import annotations

import logging
import os

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/bot.db")
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await init_tables(_db)
        logger.info("SQLite database initialized at %s", DB_PATH)
    return _db


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("SQLite database closed.")


async def init_tables(db: aiosqlite.Connection) -> None:
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            user_id TEXT PRIMARY KEY,
            plan TEXT NOT NULL DEFAULT 'testing',
            expired TEXT,
            testing_quota INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            current_process INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            active INTEGER DEFAULT 1,
            cooldown_until INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS proxies (
            proxy TEXT PRIMARY KEY,
            active INTEGER DEFAULT 1,
            cooldown_until INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            model_id TEXT,
            status TEXT DEFAULT 'processing',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS usage (
            user_id TEXT PRIMARY KEY,
            video_today INTEGER DEFAULT 0,
            last_reset TEXT,
            video_month INTEGER DEFAULT 0,
            last_month_reset TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            joined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS models_status (
            id TEXT PRIMARY KEY,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS settings (
            id TEXT PRIMARY KEY,
            data TEXT DEFAULT '{}'
        );
    """)
    await db.commit()
