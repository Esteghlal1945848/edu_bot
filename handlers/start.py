from aiogram import types
from database.core import get_db
from database.models import User
from sqlalchemy import select

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    subject_keyboard
)


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

    await message.answer(
        f"""
🎓 <b>خوش آمدید به بزرگ‌ترین آرشیو آموزشی</b>

👋 سلام {user.full_name}

از منو انتخاب کن 👇
""",
        parse_mode="HTML",
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
            "کدوم پایه‌ای؟ 👇",
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


    elif text == "🎥 ویدئو":

        await message.answer(
            "بخش ویدئو"
        )


    elif text == "👨‍🏫 دبیر":

        await message.answer(
            "بخش دبیر"
        )


    elif text == "🔍 جستجو":

        await message.answer(
            "عبارت جستجو را بفرست"
        )
