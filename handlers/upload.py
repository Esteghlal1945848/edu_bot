from aiogram import types

from database.core import get_db
from database.models import Archive

from handlers.state import upload_state


# =========================
# FILE
# =========================
async def handle_file(message: types.Message):

    user_id = message.from_user.id

    state = upload_state.get(user_id)

    if not state:
        return

    if state.get("mode") != "admin_upload":
        return

    file_id = None
    file_type = None

    if message.document:

        file_id = message.document.file_id
        file_type = "pdf"

    elif message.video:

        file_id = message.video.file_id
        file_type = "video"

    if not file_id:

        await message.answer(
            "❌ فقط PDF یا MP4 بفرست"
        )

        return

    upload_state[user_id].update({

        "file_id": file_id,

        "type": file_type,

        "step": "caption"

    })

    await message.answer(
        "✍️ حالا توضیحات رو بنویس"
    )


# =========================
# CAPTION
# =========================
async def handle_caption(message: types.Message):

    user_id = message.from_user.id

    state = upload_state.get(user_id)

    if not state:
        return

    if state.get("step") != "caption":
        return

    try:

        async for db in get_db():

            db.add(

                Archive(

                    type=state["type"],

                    grade=state["grade"],

                    major=state["major"],

                    subject=state["subject"],

                    file_id=state["file_id"],

                    caption=message.text,

                    uploaded_by=user_id

                )

            )

            await db.commit()

        upload_state.pop(
            user_id,
            None
        )

        await message.answer(
            "✅ فایل با موفقیت ذخیره شد"
        )

    except Exception as e:

        await message.answer(
            f"❌ خطا:\n{e}"
        )
