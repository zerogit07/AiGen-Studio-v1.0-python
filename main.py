"""AiGen Studio Bot — aiogram entry point."""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)


async def main() -> None:
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    from src.bot.handlers.callbacks import router as callbacks_router
    from src.bot.handlers.commands import router as commands_router
    from src.bot.handlers.messages import router as messages_router
    from src.bot.state import load_admin_ids, start_state_cleaner
    from src.core.triple_pool import triple_pool
    from src.database.apikeys import api_key_manager
    from src.database.db import close_db, get_db
    from src.database.members import member_manager
    from src.database.models import model_manager
    from src.database.proxies import proxy_manager
    from src.database.settings import landing_page_manager
    from src.database.usage import usage_manager
    from src.database.users import user_manager
    from src.services.request_engine import cleanup_sessions

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN tidak ditemukan di .env")
        sys.exit(1)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(messages_router)

    # Initialize database
    await get_db()
    logger.info("Database initialized.")

    # Load admin IDs
    load_admin_ids()

    # Load all data
    await member_manager.load_members()
    await member_manager.load_custom_limits()
    await api_key_manager.load_keys()
    await proxy_manager.load_proxies()
    await user_manager.load_users()
    await landing_page_manager.load_settings()
    await model_manager.load()

    # Build triple pool
    triple_pool.rebuild()
    logger.info("TriplePool built with %d sets.", len(triple_pool))

    # Start background tasks
    asyncio.create_task(start_state_cleaner())

    # Set bot commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Mulai / Landing Page"),
        BotCommand(command="menu", description="Menu Utama"),
        BotCommand(command="admin", description="Admin Panel"),
    ])

    logger.info("Bot starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await cleanup_sessions()
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
