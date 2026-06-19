import asyncio

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN

from handlers.start import (
    cmd_start,
    handle_buttons
)

from handlers.upload import (
    handle_file
)


bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher(
    bot,
    storage=MemoryStorage()
)


async def main():

    dp.message_handlers.handlers.clear()

    dp.register_message_handler(
        cmd_start,
        commands=["start"]
    )

    dp.register_message_handler(
        handle_buttons,
        content_types=["text"]
    )

    dp.register_message_handler(
        handle_file,
        content_types=[
            "document",
            "video"
        ]
    )

    print("BOT STARTED")

    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
