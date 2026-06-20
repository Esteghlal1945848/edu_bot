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

    if state.get("step") != "file":
        return

    file_id = None

    if message.document:

        file_id = message.document.file_id

    elif message.video:

        file_id = message.video.file_id

    if not file_id:

        await message.answer(
            "❌ فقط PDF یا ویدیو بفرست"
        )

        return

    state["file_id"] = file_id

    state["step"] = "caption"

    await message.answer(
        "✍️ توضیحات را ارسال کن"
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

            archive = Archive(

                type=state["type"],

                grade=state["grade"],

                major=state["major"],

                subject=state["subject"],

                file_id=state["file_id"],

                caption=message.text or "",

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
            "✅ ثبت شد و داخل دیتابیس ذخیره شد"
        )

    except Exception as e:

        print(e)

        await message.answer(
            f"❌ خطا:\n{str(e)}"
        )
