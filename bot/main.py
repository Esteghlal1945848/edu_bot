import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from database.core import init_db

from handlers.start import cmd_start, handle_buttons
from handlers.upload import handle_file, handle_caption


# =========================
# STARTUP
# =========================
async def on_startup(dp):
    await init_db()
    print("Database initialized - Bot started!")


# =========================
# MAIN
# =========================
async def main():

    bot = Bot(token=os.getenv("BOT_TOKEN"))

    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", "")
    )

    dp = Dispatcher(bot, storage=storage)

    # =========================
    # HANDLERS ORDER (IMPORTANT)
    # =========================

    # 1. /start
    dp.register_message_handler(cmd_start, commands=["start"])

    # 2. file upload (PDF / Video)
    dp.register_message_handler(
        handle_file,
        content_types=["document", "video"]
    )

    # 3. caption after file
    dp.register_message_handler(
        handle_caption,
        content_types=types.ContentType.TEXT
    )

    # 4. all button / menu actions (LAST)
    dp.register_message_handler(handle_buttons)

    await on_startup(dp)

    print("Bot is running!")

    try:
        await dp.start_polling()

    finally:
        await bot.session.close()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(main())
