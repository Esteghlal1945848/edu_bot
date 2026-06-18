from aiogram import types
from database.core import get_db
from database.models import User
from sqlalchemy import select


async def cmd_start(message: types.Message):
    user = message.from_user

    welcome_text = f"""
🎓 <b>خوش آمدید به بزرگ‌ترین آرشیو آموزشی</b>

👋 سلام {user.full_name} عزیز!

از منوی زیر انتخاب کنید 👇
"""

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(
        "📚 جزوه",
        "🎥 ویدئو"
    )

    keyboard.add(
        "👨‍🏫 دبیر",
        "🔍 جستجو"
    )

    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
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

    if message.text == "📚 جزوه":
        await message.answer("📚 بخش جزوه")

    elif message.text == "🎥 ویدئو":
        await message.answer("🎥 بخش ویدئو")

    elif message.text == "👨‍🏫 دبیر":
        await message.answer("👨‍🏫 بخش دبیر")

    elif message.text == "🔍 جستجو":
        await message.answer("🔍 عبارت جستجو را ارسال کنید")