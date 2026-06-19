import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from handlers import start
from database.core import init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(dp):
    await init_db()
    logger.info("Database initialized - Bot started!")


async def main():

    bot = Bot(
        token=os.getenv("BOT_TOKEN")
    )

    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        password=os.getenv("REDIS_PASSWORD")
    )

    dp = Dispatcher(
        bot,
        storage=storage
    )

    dp.register_message_handler(
        start.cmd_start,
        commands=["start"]
    )

    dp.register_message_handler(
        start.handle_buttons,
        content_types=types.ContentTypes.TEXT
    )

    await on_startup(dp)

    logger.info("Bot is running!")

    try:
        await dp.start_polling()

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
