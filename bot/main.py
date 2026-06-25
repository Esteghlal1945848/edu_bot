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


async def on_startup(dp):
    await init_db()
    print("🤖 Bot started")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Channel ID: {CHANNEL_ID}")


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
    )
    dp = Dispatcher(bot, storage=storage)

    # =====================
    # ثبت هندلرها
    # =====================

    dp.register_message_handler(cmd_start, commands=["start"])

    dp.register_message_handler(
        handle_file,
        content_types=[types.ContentType.DOCUMENT, types.ContentType.VIDEO]
    )

    dp.register_message_handler(
        handle_buttons,
        content_types=[types.ContentType.TEXT]
    )

    dp.register_callback_query_handler(handle_callback)

    await on_startup(dp)

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
