from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.core import get_db
from database.models import Publisher
from sqlalchemy import select

def grade_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
    kb.add(KeyboardButton("دوازدهم"))
    return kb

def major_keyboard(grade):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(f"رشته:{grade}|ریاضی"))
    kb.add(KeyboardButton(f"رشته:{grade}|تجربی"))
    kb.add(KeyboardButton(f"رشته:{grade}|انسانی"))
    return kb

async def institute_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    async for db in get_db():
        result = await db.execute(
            select(Publisher).where(Publisher.type == "institute")
        )
        institutes = result.scalars().all()

    added = set()
    for ins in institutes:
        kb.add(KeyboardButton(ins.name))
        added.add(ins.name)

    # پیشفرض‌هایی که توی دیتابیس نیستن (بدون کلاسینو)
    defaults = ["ماز", "آلفا اسکول", "تایتان"]
    for name in defaults:
        if name not in added:
            kb.add(KeyboardButton(name))

    return kb

async def publisher_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    async for db in get_db():
        result = await db.execute(
            select(Publisher).where(
                Publisher.type == "book_publisher"
            )
        )
        publishers = result.scalars().all()

    if publishers:
        for p in publishers:
            kb.add(KeyboardButton(p.name))
    else:
        defaults = [
            "خیلی سبز",
            "نشر الگو",
            "فرمول بیست",
            "نردبام",
            "IQ"
        ]
        for p in defaults:
            kb.add(KeyboardButton(p))

    return kb

# ========== درس‌های جزوه و ویدیو ==========
subjects = {
    "ریاضی": ["فیزیک", "شیمی", "ریاضی", "هندسه", "فارسی", "عربی", "حسابان", "گسسته", "آمار و احتمال"],
    "تجربی": ["زیست شناسی", "شیمی", "فیزیک", "ریاضی", "فارسی", "عربی"],
    "انسانی": ["علوم و فنون ادبی", "ریاضی و آمار", "جامعه شناسی", "منطق", "اقتصاد", "فارسی", 
               "روان شناسی", "فلسفه", "عربی تخصصی", "دین و زندگی", "فلسفه و منطق", "تاریخ", "جغرافیا", "دینی"]
}

def subject_keyboard(grade, major):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for s in subjects.get(major, []):
        kb.add(KeyboardButton(s))
    return kb

# ========== کتاب‌های کمک آموزشی (از دیتابیس) ==========
async def book_subject_keyboard(publisher, grade, major):
    from database.core import get_db
    from database.models import Publisher
    from sqlalchemy import select
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    async for db in get_db():
        result = await db.execute(
            select(Publisher).where(
                Publisher.name == publisher
            )
        )

        pub = result.scalar_one_or_none()

        if pub:
            data = pub.subjects_by_grade or {}
            if grade in data and major in data[grade]:
                for subject in data[grade][major]:
                    kb.add(KeyboardButton(subject))
                return kb

    # اگر ناشر در دیتابیس نبود یا درسی نداشت، از پیشفرض استفاده کن
    defaults = {
        "ریاضی": [
            "ریاضی",
            "فیزیک",
            "شیمی",
            "هندسه"
        ],
        "تجربی": [
            "زیست شناسی",
            "فیزیک",
            "شیمی",
            "ریاضی"
        ]
    }

    for s in defaults.get(major, []):
        kb.add(KeyboardButton(s))

    return kb

async def book_publisher_keyboard(grade, major):
    from database.core import get_db
    from database.models import Publisher
    from sqlalchemy import select
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    async for db in get_db():
        result = await db.execute(
            select(Publisher).where(Publisher.type == "book_publisher")
        )
        publishers = result.scalars().all()

    # همه ناشران book_publisher رو نشون بده
    added = set()
    for pub in publishers:
        if pub.name not in added:
            kb.add(KeyboardButton(pub.name))
            added.add(pub.name)

    # پیشفرض‌هایی که توی دیتابیس نیستن
    defaults = ["خیلی سبز", "نشر الگو", "فرمول بیست", "نردبام", "IQ"]
    for name in defaults:
        if name not in added:
            kb.add(KeyboardButton(name))

    kb.add(KeyboardButton("❌ لغو"))
    return kb
