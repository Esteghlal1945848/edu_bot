from aiogram import types

from database.core import get_db
from database.models import Archive


upload_state = {}


# =========================
# گرفتن فایل (PDF / Video)
# =========================
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


    # ذخیره موقت برای مرحله caption
    upload_state[user_id] = {

        "grade": state["grade"],
        "major": state["major"],
        "subject": state["subject"],
        "file_id": file_id,
        "type": file_type,
        "step": "caption"
    }


    await message.answer("✍️ حالا توضیح (caption) رو بنویس")


# =========================
# گرفتن توضیح (caption)
# =========================
async def handle_caption(message: types.Message):

    user_id = message.from_user.id

    if user_id not in upload_state:
        return


    state = upload_state[user_id]


    if state.get("step") != "caption":
        return


    caption = message.text


    async for db in get_db():

        db.add(

            Archive(

                type=state["type"],
                grade=state["grade"],
                major=state["major"],
                subject=state["subject"],
                file_id=state["file_id"],
                caption=caption,
                uploaded_by=user_id
            )
        )

        await db.commit()


    upload_state.pop(user_id, None)


    await message.answer("✅ فایل با موفقیت ذخیره شد")
