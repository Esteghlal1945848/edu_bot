from aiogram import types
from database.core import get_db
from database.models import User
from sqlalchemy import select

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    subject_keyboard
)

# ✅ آیدی عددی خودت اینجاست
ADMIN_ID = 123456789


# =========================
# /start
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
        keyboard.add("👑 پنل ادمین")

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


# =========================
# دکمه‌ها
# =========================
async def handle_buttons(message: types.Message):

    text = message.text

    # =================
    # کاربر
    # =================

    if text == "📚 جزوه":

        await message.answer(
            "کدوم پایه‌ای؟",
            reply_markup=grade_keyboard()
        )


    elif text == "🎥 ویدئو":

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

        data = text.replace("رشته:", "")
        grade, major = data.split("|")

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(grade, major)
        )


    # =================
    # پنل ادمین
    # =================

    elif text == "👑 پنل ادمین":

        if str(message.from_user.id) != str(ADMIN_ID):
            return

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add("📤 آپلود جزوه")
        keyboard.add("🎥 آپلود ویدئو")
        keyboard.add("🔙 برگشت")

        await message.answer(
            "👑 پنل مدیریت",
            reply_markup=keyboard
        )


    # ---------- جزوه ----------

    elif text == "📤 آپلود جزوه":

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add("آپلود جزوه | دهم")
        keyboard.add("آپلود جزوه | یازدهم")
        keyboard.add("آپلود جزوه | دوازدهم")

        await message.answer(
            "جزوه برای کدوم پایه است؟",
            reply_markup=keyboard
        )


    elif text.startswith("آپلود جزوه |"):

        grade = text.split("|")[1].strip()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add(f"{grade}|ریاضی")
        keyboard.add(f"{grade}|تجربی")
        keyboard.add(f"{grade}|انسانی")

        await message.answer(
            "رشته رو انتخاب کن",
            reply_markup=keyboard
        )


    # ---------- ویدئو ----------

    elif text == "🎥 آپلود ویدئو":

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add("آپلود ویدئو | دهم")
        keyboard.add("آپلود ویدئو | یازدهم")
        keyboard.add("آپلود ویدئو | دوازدهم")

        await message.answer(
            "ویدئو برای کدوم پایه است؟",
            reply_markup=keyboard
        )


    elif text.startswith("آپلود ویدئو |"):

        grade = text.split("|")[1].strip()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        keyboard.add(f"{grade}|ریاضی")
        keyboard.add(f"{grade}|تجربی")
        keyboard.add(f"{grade}|انسانی")

        await message.answer(
            "رشته رو انتخاب کن",
            reply_markup=keyboard
        )


    # ---------- درس ----------

    elif text.count("|") == 1:

        grade, major = text.split("|")

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(grade, major)
        )


    elif text in [
        "فیزیک", "شیمی", "ریاضی", "هندسه",
        "ادبیات", "عربی", "زیست", "منطق",
        "اقتصاد", "تاریخ", "ریاضی و آمار",
        "فارسی", "حسابان", "آمار و احتمال",
        "جغرافیا", "جامعه شناسی", "روان شناسی",
        "فلسفه", "گسسته"
    ]:

        await message.answer(
            "فایل را ارسال کن 📎\n\nجزوه → PDF\nویدئو → MP4"
        )
