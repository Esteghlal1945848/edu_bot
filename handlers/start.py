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


    # USER

    if text in ["📚 جزوه", "🎥 ویدئو"]:

        await message.answer(
            "کدوم پایه؟",
            reply_markup=grade_keyboard()
        )

        return


    elif text in [

        "دهم",
        "یازدهم",
        "دوازدهم"

    ]:

        await message.answer(
            "رشته رو انتخاب کن 👇",
            reply_markup=major_keyboard(text)
        )

        return


    elif text.startswith("رشته:"):

        grade, major = text.replace(
            "رشته:",
            ""
        ).split("|")

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )

        return


    # ADMIN

    elif text == "👑 پنل ادمین":

        if str(user_id) != str(ADMIN_ID):
            return

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            "📤 آپلود جزوه"
        )

        keyboard.add(
            "🎥 آپلود ویدئو"
        )

        await message.answer(
            "👑 پنل مدیریت",
            reply_markup=keyboard
        )

        return


    elif text in [

        "📤 آپلود جزوه",
        "🎥 آپلود ویدئو"

    ]:

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        prefix = (
            "آپلود جزوه"
            if text == "📤 آپلود جزوه"
            else "آپلود ویدئو"
        )

        keyboard.add(
            f"{prefix} | دهم"
        )

        keyboard.add(
            f"{prefix} | یازدهم"
        )

        keyboard.add(
            f"{prefix} | دوازدهم"
        )

        await message.answer(
            "پایه رو انتخاب کن 👇",
            reply_markup=keyboard
        )

        return


    elif (
        text.startswith("آپلود جزوه |")
        or
        text.startswith("آپلود ویدئو |")
    ):

        grade = text.split("|")[1].strip()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            f"{grade}|ریاضی"
        )

        keyboard.add(
            f"{grade}|تجربی"
        )

        keyboard.add(
            f"{grade}|انسانی"
        )

        await message.answer(
            "رشته رو انتخاب کن 👇",
            reply_markup=keyboard
        )

        return


    elif "|" in text:

        grade, major = text.split("|")

        upload_state[user_id] = {

            "mode": "admin_upload",

            "grade": grade,

            "major": major

        }

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )

        return


    elif text in [

        "فیزیک",
        "شیمی",
        "ریاضی",
        "زیست",
        "فارسی",
        "عربی",
        "هندسه"

    ]:

        if user_id not in upload_state:
            return

        upload_state[user_id][
            "subject"
        ] = text

        await message.answer(
            "📎 فایل رو بفرست"
        )
