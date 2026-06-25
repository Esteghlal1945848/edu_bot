import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from database.core import get_db, init_db
from database.models import Archive

from handlers.start import cmd_start, handle_buttons, handle_file, handle_callback
from aiogram.types import KeyboardButton


ADMIN_ID = 7336595194
CHANNEL_ID = -1003918140957


# =========================
# STARTUP
# =========================
async def on_startup(dp):
    await init_db()
    print("🤖 Bot started")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Channel ID: {CHANNEL_ID}")


# =========================
# MAIN
# =========================
async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
    )
    dp = Dispatcher(bot, storage=storage)

    # =====================
    # ثبت هندلرها (با اولویت درست)
    # =====================

    # 1️⃣ استارت
    dp.register_message_handler(cmd_start, commands=["start"])

    # 2️⃣ همه فایل‌ها (کانال + ادمین) - یه هندلر واحد
    dp.register_message_handler(
        handle_file,
        content_types=[types.ContentType.DOCUMENT, types.ContentType.VIDEO]
    )

    # 3️⃣ دکمه‌ها و پیام‌های متنی
    dp.register_message_handler(
        handle_buttons,
        content_types=[types.ContentType.TEXT]
    )

    # 4️⃣ هندلر Callback (برای صفحه‌بندی و ...)
    dp.register_callback_query_handler(handle_callback)

    await on_startup(dp)

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
