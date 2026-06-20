from aiogram import types

from database.core import get_db
from database.models import Archive
from handlers.state import upload_state


async def handle_file(message: types.Message):

    user_id = message.from_user.id

    state = upload_state.get(user_id)

    if not state:
        return

    if state.get("mode") != "admin_upload":
        return

    if state.get("step") != "file":
        return


    if message.document:

        file_id = message.document.file_id
        file_type = "pdf"

    elif message.video:

        file_id = message.video.file_id
        file_type = "video"

    else:

        await message.answer(
            "❌ فقط فایل بفرست"
        )

        return


    try:

        async for db in get_db():

            db.add(

                Archive(

                    type=file_type,

                    grade=state["grade"],

                    major=state["major"],

                    subject=state["subject"],

                    file_id=file_id,

                    caption=message.caption or "",

                    uploaded_by=user_id
                )
            )

            await db.commit()


        upload_state.pop(
            user_id,
            None
        )

        await message.answer(
            "✅ جزوه ثبت شد و داخل دیتابیس ذخیره شد"
        )

    except Exception as e:

        await message.answer(
            f"❌ خطا:\n{str(e)}"
        )
