from aiogram import types
from database.core import get_db
from database.models import Archive

# =========================
# TEMP STATE
# =========================
upload_state = {}


# =========================
# STEP 1: RECEIVE FILE (ADMIN)
# =========================
async def handle_file(message: types.Message):
    user_id = message.from_user.id

    state = upload_state.get(user_id)

    # ❌ اگر وارد flow نشده، هیچ کاری نکن
    if not state:
        return

    # ❌ فقط مخصوص ادمین آپلود
    if state.get("mode") != "admin_upload":
        return

    file_id = None
    file_type = None

    # گرفتن فایل
    if message.document:
        file_id = message.document.file_id
        file_type = "pdf"

    elif message.video:
        file_id = message.video.file_id
        file_type = "video"

    if not file_id:
        await message.answer("❌ فقط PDF یا MP4 بفرست")
        return

    # رفتن به مرحله caption
    upload_state[user_id] = {
        "mode": "admin_upload",
        "grade": state["grade"],
        "major": state["major"],
        "subject": state["subject"],
        "file_id": file_id,
        "type": file_type,
        "step": "caption"
    }

    await message.answer("✍️ حالا توضیحات (caption) رو بنویس")


# =========================
# STEP 2: RECEIVE CAPTION
# =========================
async def handle_caption(message: types.Message):
    user_id = message.from_user.id

    state = upload_state.get(user_id)

    if not state:
        return

    # فقط مرحله caption
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
          try: 
    await db.commit()

    upload_state.pop(user_id, None)

    await message.answer(
        "✅ فایل با موفقیت ذخیره شد"
    )

except Exception as e:

    await message.answer(
        f"❌ خطا:\n{str(e)}"
    )

    # پاک کردن state
    upload_state.pop(user_id, None)

    await message.answer("✅ فایل با موفقیت ذخیره شد")


# =========================
# STEP 0: START UPLOAD (ADMIN ONLY)
# اینو باید از دکمه "جزوه دهم شیمی" صدا بزنی
# =========================
async def start_admin_upload(message: types.Message, grade: int, major: str, subject: str):
    user_id = message.from_user.id

    upload_state[user_id] = {
        "mode": "admin_upload",
        "grade": grade,
        "major": major,
        "subject": subject,
        "step": "file"
    }

    await message.answer("📂 حالا فایل PDF یا ویدئو رو بفرست")
