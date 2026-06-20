from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# =====================
# پایه
# =====================
def grade_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("دهم"),
        KeyboardButton("یازدهم")
    )

    kb.add(
        KeyboardButton("دوازدهم")
    )

    return kb


# =====================
# رشته
# =====================
def major_keyboard(grade):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton(f"رشته:{grade}|ریاضی"))
    kb.add(KeyboardButton(f"رشته:{grade}|تجربی"))
    kb.add(KeyboardButton(f"رشته:{grade}|انسانی"))

    return kb


# =====================
# موسسه
# =====================
def institute_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("ماز"))
    kb.add(KeyboardButton("آلفا اسکول"))
    kb.add(KeyboardButton("تایتان"))
    kb.add(KeyboardButton("کلاسینو"))

    return kb


# =====================
# درس‌ها
# =====================
subjects = {
    "دهم": {
        "ریاضی": ["فیزیک", "شیمی", "ریاضی", "هندسه", "ادبیات", "عربی"],
        "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست", "ادبیات", "عربی"],
        "انسانی": ["منطق", "اقتصاد", "تاریخ", "ریاضی و آمار", "عربی"]
    },

    "یازدهم": {
        "ریاضی": ["فیزیک", "فارسی", "شیمی", "هندسه", "حسابان", "آمار و احتمال"],
        "تجربی": ["فیزیک", "شیمی", "ریاضی", "فارسی", "زیست"],
        "انسانی": ["عربی", "ریاضی و آمار", "جغرافیا", "تاریخ", "جامعه شناسی", "روان شناسی", "فلسفه"]
    },

    "دوازدهم": {
        "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "گسسته", "فارسی"],
        "تجربی": ["فارسی", "شیمی", "فیزیک", "ریاضی", "زیست"],
        "انسانی": ["ریاضی و آمار", "جغرافیا", "تاریخ", "جامعه شناسی", "فلسفه"]
    }
}


def subject_keyboard(grade, major, institute=None):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for s in subjects[grade][major]:
        kb.add(KeyboardButton(s))

    return kb
