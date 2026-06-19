import asyncio

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN

from handlers import start
from handlers.upload import handle_file


bot = Bot(token=BOT_TOKEN)

storage = MemoryStorage()

dp = Dispatcher(
    bot,
    storage=storage
)


async def main():

    dp.register_message_handler(
        start.cmd_start,
        commands=["start"]
    )

    dp.register_message_handler(
        start.handle_buttons,
        content_types=["text"]
    )

    dp.register_message_handler(
        handle_file,
        content_types=["document", "video"]
    )

    print("BOT STARTED")

    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
