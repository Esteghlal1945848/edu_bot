from aiogram import types
from sqlalchemy import select

from database.core import get_db
from database.models import User

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    subject_keyboard
)

from handlers.state import upload_state


ADMIN_ID = 7336595194


# =========================
# START
# =========================
async def cmd_start(message: types.Message):

    user = message.from_user

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        "📚 جزوه",
        "🎥 ویدئو"
    )

    keyboard.add(
        "👨‍🏫 دبیر",
        "🔍 جستجو"
    )

    if str(user.id) == str(ADMIN_ID):

        keyboard.add(
            "👑 پنل ادمین"
        )

    await message.answer(
        f"""
🎓 خوش آمدی {user.full_name}

📚 بزرگ‌ترین آرشیو جزوه و ویدئو

از منو انتخاب کن 👇
""",
        reply_markup=keyboard
    )

    async for db in get_db():

        result = await db.execute(
            select(User).where(
                User.telegram_id == user.id
            )
        )

        existing = result.scalar_one_or_none()

        if not existing:

            db.add(
                User(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )
            )

            await db.commit()


# =========================
# BUTTONS
# =========================
async def handle_buttons(message: types.Message):

    text = message.text or ""

    user_id = message.from_user.id


    # =====================
    # ADMIN PANEL
    # =====================

    if text == "👑 پنل ادمین":

        if str(user_id) != str(ADMIN_ID):
            return

        kb = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add("📤 آپلود جزوه")

        kb.add("🎥 آپلود ویدئو")

        await message.answer(
            "👑 پنل مدیریت",
            reply_markup=kb
        )

        return


    # =====================
    # START UPLOAD
    # =====================

    elif text in [

        "📤 آپلود جزوه",
        "🎥 آپلود ویدئو"

    ]:

        upload_state[user_id] = {

            "mode": "admin_upload",

            "type": (
                "pdf"
                if text == "📤 آپلود جزوه"
                else "video"
            ),

            "step": "grade"
        }

        await message.answer(
            "پایه را انتخاب کن 👇",
            reply_markup=grade_keyboard()
        )

        return


    # =====================
    # GRADE
    # =====================

    elif text in [

        "دهم",
        "یازدهم",
        "دوازدهم"

    ]:

        if user_id in upload_state:

            upload_state[user_id]["grade"] = text

            upload_state[user_id]["step"] = "major"

        await message.answer(
            "رشته را انتخاب کن 👇",
            reply_markup=major_keyboard(text)
        )

        return


    # =====================
    # MAJOR
    # =====================

    elif text.startswith("رشته:"):

        grade, major = text.replace(
            "رشته:",
            ""
        ).split("|")

        if user_id in upload_state:

            upload_state[user_id]["grade"] = grade

            upload_state[user_id]["major"] = major

            upload_state[user_id]["step"] = "subject"

        await message.answer(
            "درس را انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )

        return


    # =====================
    # SUBJECT
    # =====================

    elif user_id in upload_state:

        state = upload_state[user_id]

        if state.get("step") == "subject":

            state["subject"] = text

            state["step"] = "file"

            await message.answer(
                "📎 فایل PDF یا MP4 را ارسال کن"
            )

            return


    # =====================
    # USER MODE
    # =====================

    elif text in [

        "📚 جزوه",
        "🎥 ویدئو"

    ]:

        await message.answer(
            "کدوم پایه؟",
            reply_markup=grade_keyboard()
        )

        return
