from aiogram import types
from database.core import get_db
from database.models import User
from sqlalchemy import select

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    subject_keyboard
)

from handlers.upload import upload_state


ADMIN_ID = 7336595194


async def cmd_start(message: types.Message):

    user = message.from_user

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("📚 جزوه", "🎥 ویدئو")
    keyboard.add("👨‍🏫 دبیر", "🔍 جستجو")

    if str(user.id) == str(ADMIN_ID):
        keyboard.add("👑 پنل ادمین")

    await message.answer(
        f"🎓 خوش آمدی {user.full_name}",
        reply_markup=keyboard
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


async def handle_buttons(message: types.Message):

    text = message.text

    if text == "👑 پنل ادمین":

        if message.from_user.id != ADMIN_ID:
            return

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("📤 آپلود جزوه")
        keyboard.add("🎥 آپلود ویدئو")

        await message.answer("پنل مدیریت", reply_markup=keyboard)


    elif text in ["فیزیک","شیمی","ریاضی","هندسه","ادبیات","عربی","زیست","منطق",
                  "اقتصاد","تاریخ","ریاضی و آمار","فارسی","حسابان","آمار و احتمال",
                  "جغرافیا","جامعه شناسی","روان شناسی","فلسفه","گسسته"]:

        if message.from_user.id != ADMIN_ID:
            await message.answer("دسترسی نداری ❌")
            return

        upload_state[message.from_user.id] = {
            "grade": "نامشخص",
            "major": "نامشخص",
            "subject": text
        }

        await message.answer("فایل (PDF یا MP4) رو بفرست 📎")
