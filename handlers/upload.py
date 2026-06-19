from aiogram import types
from database.core import get_db
from database.models import Archive

upload_state = {}


async def handle_file(message: types.Message):

    user_id = message.from_user.id

    if user_id not in upload_state:
        return

    state = upload_state[user_id]

    file_id = None
    file_type = None

    if message.document:
        file_id = message.document.file_id
        file_type = "pdf"

    elif message.video:
        file_id = message.video.file_id
        file_type = "video"

    if not file_id:
        await message.answer("فقط PDF یا MP4 بفرست")
        return

    async for db in get_db():

        db.add(
            File(
                file_id=file_id,
                file_type=file_type,
                grade=state["grade"],
                major=state["major"],
                subject=state["subject"]
            )
        )

        await db.commit()

    await message.answer("فایل ذخیره شد ✅")
