from aiogram import types
from database.core import get_db
from database.models import Archive

# =========================
# TEMP STATE (simple FSM)
# =========================
upload_state = {}


# =========================
# STEP 1: RECEIVE FILE
# =========================
async def handle_file(message: types.Message):
    user_id = message.from_user.id

    # اگر کاربر وارد مرحله آپلود نشده
    if user_id not in upload_state:
        return

    state = upload_state[user_id]

    file_id = None
    file_type = None

    # بررسی نوع فایل
    if message.document:
        file_id = message.document.file_id
        file_type = "pdf"

    elif message.video:
        file_id = message.video.file_id
        file_type = "video"

    if not file_id:
        await message.answer("❌ فقط PDF یا MP4 بفرست")
        return

    # ذخیره مرحله بعد (caption)
    upload_state[user_id] = {
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

    # اگر اصلاً وارد flow نشده
    if user_id not in upload_state:
        return

    state = upload_state[user_id]

    # فقط وقتی در مرحله caption هستیم
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

    # پاک کردن state
    upload_state.pop(user_id, None)

    await message.answer("✅ فایل با موفقیت ذخیره شد")


# =========================
# OPTIONAL: START UPLOAD FLOW
# (اگر دکمه "آپلود" داری)
# =========================
async def start_upload(message: types.Message, grade: str, major: str, subject: str):
    user_id = message.from_user.id

    upload_state[user_id] = {
        "grade": grade,
        "major": major,
        "subject": subject,
        "step": "file"
    }

    await message.answer("📂 حالا فایل PDF یا ویدئو رو بفرست")
