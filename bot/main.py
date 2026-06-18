import asyncio
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from database.core import init_db
from handlers import start


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def on_startup(dp):
    await init_db()
    logger.info("Database initialized - Bot started!")


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", "")
    )

    dp = Dispatcher(bot, storage=storage)

    dp.register_message_handler(
        start.cmd_start,
        commands=["start"]
    )
    
    dp.register_message_handler(
        start.handle_buttons
    )

    await on_startup(dp)

    logger.info("Bot is running!")

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())