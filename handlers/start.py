from aiogram import types
from database.core import get_db
from database.models import User
from sqlalchemy import select

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    subject_keyboard
)

ADMIN_ID = 123456789


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

    if user.id == ADMIN_ID:

        keyboard.add(
            "👑 پنل ادمین"
        )

    await message.answer(
        f"""
🎓 خوش آمدی {user.full_name}

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


async def handle_buttons(message: types.Message):

    text = message.text


    if text == "📚 جزوه":

        await message.answer(
            "کدوم پایه‌ای؟",
            reply_markup=grade_keyboard()
        )


    elif text in ["دهم", "یازدهم", "دوازدهم"]:

        await message.answer(
            "رشته رو انتخاب کن 👇",
            reply_markup=major_keyboard(text)
        )


    elif text.startswith("رشته:"):

        data = text.replace(
            "رشته:",
            ""
        )

        grade, major = data.split("|")

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )


    elif text == "👑 پنل ادمین":

        if message.from_user.id != ADMIN_ID:
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

        keyboard.add(
            "🔙 برگشت"
        )

        await message.answer(
            "پنل مدیریت",
            reply_markup=keyboard
        )


    elif text == "📤 آپلود جزوه":

        if message.from_user.id != ADMIN_ID:
            return

        await message.answer(
            "جزوه برای کدوم پایه است؟",
            reply_markup=grade_keyboard()
        )
