from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def grade_keyboard():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        KeyboardButton("دهم"),
        KeyboardButton("یازدهم")
    )

    kb.add(
        KeyboardButton("دوازدهم")
    )

    return kb
