from aiogram import types

from database.core import get_db
from database.models import Archive


# =========================
# TEMP STATE
# =========================
upload_state = {}


# =========================
# STEP 1 — RECEIVE FILE
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

    upload_state[user_id] = {

        "mode": "admin_upload",

        "grade": state["grade"],

        "major": state["major"],

        "subject": state["subject"],

        "file_id": file_id,

        "type": file_type,

        "step": "caption"
    }

    await message.answer(
        "✍️ حالا توضیحات رو بنویس"
    )


# =========================
# STEP 2 — RECEIVE CAPTION
# =========================
async def handle_caption(message: types.Message):

    user_id = message.from_user.id

    state = upload_state.get(user_id)

    if not state:
        return

    if state.get("step") != "caption":
        return

    caption = message.text

    try:

        async for db in get_db():

            archive = Archive(

                type=state["type"],

                grade=state["grade"],

                major=state["major"],

                subject=state["subject"],

                file_id=state["file_id"],

                caption=caption,

                uploaded_by=user_id
            )

            db.add(
                archive
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
            f"❌ ذخیره نشد:\n{str(e)}"
        )
