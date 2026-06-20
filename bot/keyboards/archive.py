from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# =========================
# پایه
# =========================
def grade_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("دهم"),
        KeyboardButton("یازدهم")
    )

    kb.add(
        KeyboardButton("دوازدهم")
    )

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
# درس‌ها (فعلاً ساده)
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
# دبیر (مهم!)
# =========================
def teacher_keyboard(grade, major, institute, subject):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    # ================= MAZ =================
    if institute == "ماز":

        data = {
            ("ریاضی", "فیزیک"): ["محمدرضا شجاعی"],
            ("ریاضی", "شیمی"): ["فرشاد هادیان فرد", "محمدعلی مومن زاده"],
            ("تجربی", "زیست"): ["امید غلامی", "پوریا خیراندیش"],
            ("انسانی", "علوم و فنون"): ["عماد فیض آبادی", "علیرضا بدیع"],
            ("انسانی", "ریاضی و آمار"): ["محمد یگانه", "علی فضلی خانی"],
            ("انسانی", "جامعه شناسی"): ["مژده طالب"],
            ("انسانی", "منطق"): ["محمدمهدی تفقدی"],
        }

        teachers = data.get((major, subject), ["دبیر ثبت نشده"])

    # ================= ALPHA =================
    elif institute == "آلفا اسکول":

        data = {
            "فیزیک": ["میری"],
            "شیمی": ["طهرانچی"],
            "ریاضی": ["کرمی"],
            "زیست": ["زرندی"]
        }

        teachers = data.get(subject, ["دبیر ثبت نشده"])

    # ================= TITAN =================
    elif institute == "تایتان":

        if subject == "شیمی":
            teachers = ["فراهانی"]
        else:
            teachers = ["دبیر ثبت نشده"]

    # ================= CLASSINO =================
    elif institute == "کلاسینو":

        data = {
            "فیزیک": ["نوکنده", "براتی"],
            "شیمی": ["مرادی"],
            "ریاضی": ["بابک سادات", "حمید پوراشرف"],
            "زیست": ["حنیف", "فرهمند"]
        }

        teachers = data.get(subject, ["دبیر ثبت نشده"])

    else:
        teachers = ["دبیر ثبت نشده"]

    for t in teachers:
        kb.add(KeyboardButton(t))

    return kb
