from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# =========================
# پایه
# =========================
def grade_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("دهم"),
        KeyboardButton("یازدهم")
    )

    kb.add(KeyboardButton("دوازدهم"))

    return kb


# =========================
# رشته
# =========================
def major_keyboard(grade):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton(f"رشته:{grade}|ریاضی"))
    kb.add(KeyboardButton(f"رشته:{grade}|تجربی"))
    kb.add(KeyboardButton(f"رشته:{grade}|انسانی"))

    return kb


# =========================
# موسسه
# =========================
def institute_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("ماز")
    kb.add("آلفا اسکول")
    kb.add("تایتان")
    kb.add("کلاسینو")

    return kb


# =========================
# درس‌ها
# =========================
subjects = {
    "ریاضی": ["فیزیک", "شیمی", "ریاضی", "هندسه", "فارسی", "عربی"],
    "تجربی": ["زیست", "شیمی", "فیزیک", "ریاضی", "فارسی", "عربی"],
    "انسانی": ["علوم و فنون", "ریاضی و آمار", "جامعه شناسی", "منطق", "اقتصاد", "فارسی"]
}


def subject_keyboard(grade, major):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for s in subjects.get(major, []):
        kb.add(KeyboardButton(s))

    return kb


# =========================
# دبیر
# =========================
def teacher_keyboard(grade, major, institute, subject):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    data = {
        "ماز": {
            ("ریاضی", "فیزیک"): ["شجاعی"],
            ("ریاضی", "شیمی"): ["فرشاد هادیان فرد", "مومن زاده"],
            ("تجربی", "زیست"): ["پوریا خیراندیش", "امید غلامی"],
        },
        "کلاسینو": {
            "فیزیک": ["نوکنده", "براتی"],
            "شیمی": ["مرادی"],
            "زیست": ["حنیف", "فرهمند"]
        },
        "آلفا اسکول": {
            "فیزیک": ["میری"],
            "شیمی": ["طهرانچی"],
            "ریاضی": ["کرمی"]
        },
        "تایتان": {
            "شیمی": ["فراهانی"]
        }
    }

    teachers = []

    inst_data = data.get(institute, {})

    if isinstance(inst_data, dict):

        if institute == "ماز":
            teachers = inst_data.get((major, subject), [])

        else:
            teachers = inst_data.get(subject, [])

    for t in teachers:
        kb.add(KeyboardButton(t))

    return kb
            
