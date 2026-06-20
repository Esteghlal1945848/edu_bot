from aiogram import types
from sqlalchemy import select

from database.core import get_db
from database.models import User

from bot.data.teachers import TEACHERS
from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    institute_keyboard,
    subject_keyboard,
    teacher_keyboard
)

from handlers.state import upload_state


ADMIN_ID = 7336595194


# =========================
# START
# =========================
async def cmd_start(message: types.Message):

    user = message.from_user

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        "📚 جزوه",
        "🎥 ویدئو"
    )

    if str(user.id) == str(ADMIN_ID):
        kb.add("👑 پنل ادمین")

    await message.answer(
        "🎓 خوش اومدی",
        reply_markup=kb
    )

    async for db in get_db():

        result = await db.execute(
            select(User).where(User.telegram_id == user.id)
        )

        if not result.scalar_one_or_none():

            db.add(
                User(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )
            )

            await db.commit()


# =========================
# HANDLER
# =========================
async def handle_buttons(message: types.Message):

    text = message.text
    user_id = message.from_user.id


    # =====================
    # ADMIN PANEL
    # =====================
    if text == "👑 پنل ادمین":

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add("📤 آپلود جزوه")
        kb.add("🎥 آپلود ویدئو")

        await message.answer(
            "پنل مدیریت",
            reply_markup=kb
        )
        return


    # =====================
    # START UPLOAD
    # =====================
    elif text in ["📤 آپلود جزوه", "🎥 آپلود ویدئو"]:

        upload_state[user_id] = {
            "mode": "admin_upload",
            "type": "pdf" if text == "📤 آپلود جزوه" else "video",
            "step": "grade"
        }

        await message.answer(
            "پایه را انتخاب کن",
            reply_markup=grade_keyboard()
        )
        return


    # =====================
    # GRADE
    # =====================
    elif text in ["دهم", "یازدهم", "دوازدهم"]:

        if user_id in upload_state:
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"

        await message.answer(
            "رشته را انتخاب کن",
            reply_markup=major_keyboard(text)
        )
        return


    # =====================
    # MAJOR
    # =====================
    elif text.startswith("رشته:"):

        grade, major = text.replace("رشته:", "").split("|")

        if user_id in upload_state:
            upload_state[user_id]["grade"] = grade
            upload_state[user_id]["major"] = major
            upload_state[user_id]["step"] = "institute"

        await message.answer(
            "🏛 موسسه را انتخاب کن",
            reply_markup=institute_keyboard()
        )
        return


    # =====================
    # INSTITUTE
    # =====================
    elif text in ["ماز", "آلفا اسکول", "تایتان", "کلاسینو"]:

        state = upload_state[user_id]

        state["institute"] = text
        state["step"] = "subject"

        await message.answer(
            "📚 درس را انتخاب کن",
            reply_markup=subject_keyboard(
                state["grade"],
                state["major"]
            )
        )
        return


    # =====================
    # SUBJECT -> TEACHERS
    # =====================
    elif user_id in upload_state:

        state = upload_state[user_id]

        if state.get("step") == "subject":

            subject = text
            state["subject"] = subject
            state["step"] = "teacher"

            teachers = TEACHERS.get(
                state["institute"],
                {}
            ).get(
                state["grade"],
                {}
            ).get(
                state["major"],
                {}
            ).get(
                subject,
                []
            )

            if not teachers:
                await message.answer("❌ دبیر پیدا نشد")
                return

            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

            for t in teachers:
                kb.add(t)

            await message.answer(
                "👨‍🏫 دبیر را انتخاب کن",
                reply_markup=kb
            )
            return


    # =====================
    # USER MODE
    # =====================
    elif text in ["📚 جزوه", "🎥 ویدئو"]:

        await message.answer(
            "کدوم پایه؟",
            reply_markup=grade_keyboard()
        )
        return
