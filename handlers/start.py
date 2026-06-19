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


async def cmd_start(message: types.Message):

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        "📚 جزوه",
        "🎥 ویدئو"
    )

    if str(message.from_user.id) == str(ADMIN_ID):

        keyboard.add(
            "👑 پنل ادمین"
        )

    await message.answer(
        "خوش اومدی 👇",
        reply_markup=keyboard
    )



async def handle_buttons(message: types.Message):

    text = message.text

    if text == "👑 پنل ادمین":

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            "📤 آپلود جزوه"
        )

        await message.answer(
            "پنل مدیریت",
            reply_markup=keyboard
        )


    elif text == "📤 آپلود جزوه":

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            "دهم|ریاضی"
        )

        await message.answer(
            "انتخاب کن"
        )


    elif "|" in text:

        grade, major = text.split("|")

        upload_state[
            message.from_user.id
        ] = {

            "mode": "admin_upload",

            "grade": grade,

            "major": major
        }

        await message.answer(
            "درس رو انتخاب کن"
        )


    elif text == "شیمی":

        upload_state[
            message.from_user.id
        ]["subject"] = "شیمی"

        await message.answer(
            "📎 فایل بفرست"
        )
