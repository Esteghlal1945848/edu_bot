import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import (
    RedisStorage2
)

from database.core import init_db

from handlers.start import (
    cmd_start,
    handle_buttons,
    handle_file  # از start.py import میکنیم
)


# =========================
# STARTUP
# =========================
async def on_startup(dp):

    await init_db()

    print("Bot started")


# =========================
# MAIN
# =========================
async def main():

    bot = Bot(
        token=os.getenv(
            "BOT_TOKEN"
        )
    )

    storage = RedisStorage2(

        host=os.getenv(
            "REDIS_HOST",
            "redis"
        ),

        port=int(
            os.getenv(
                "REDIS_PORT",
                6379
            )
        ),

        password=os.getenv(
            "REDIS_PASSWORD",
            ""
        )
    )

    dp = Dispatcher(
        bot,
        storage=storage
    )

    # start
    dp.register_message_handler(
        cmd_start,
        commands=["start"]
    )

    # فایل
    dp.register_message_handler(
        handle_file,
        content_types=[
            "document",
            "video"
        ]
    )

    # دکمه‌ها
    dp.register_message_handler(
        handle_buttons
    )

    await on_startup(dp)

    try:

        await dp.start_polling()

    finally:

        await bot.session.close()


# =========================
# RUN
# =========================
if __name__ == "__main__":

    asyncio.run(main())
