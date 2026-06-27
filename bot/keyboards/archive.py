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

# ========== کتاب‌های کمک آموزشی ==========
book_subjects = {
    "فرمول بیست": {
        "دهم": {
            "ریاضی": ["شیمی", "هندسه", "فیزیک", "فارسی", "دین و زندگی", "عربی", "جغرافیا"],
            "تجربی": ["زیست", "شیمی", "ریاضی", "فیزیک", "فارسی", "دین و زندگی", "عربی", "جغرافیا"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "دین و زندگی", "فارسی", "عربی", "تاریخ", "شیمی", "زمین شناسی", "انسان و محیط زیست"],
            "تجربی": ["دین و زندگی", "فارسی", "عربی", "فیزیک", "شیمی", "ریاضی", "تاریخ", "زمین شناسی", "انسان و محیط زیست"]
        },
        "دوازدهم": {
            "ریاضی": ["هندسه", "گسسته", "زبان", "فیزیک", "ادبیات", "عربی", "دینی", "شیمی", "حسابان"],
            "تجربی": ["زیست", "زبان", "فیزیک", "ادبیات", "عربی", "دینی", "شیمی", "ریاضی"]
        }
    },
    "IQ": {
        "دهم": {
            "ریاضی": ["شیمی", "ریاضی", "فیزیک"],
            "تجربی": ["زیست", "شیمی", "ریاضی", "فیزیک"]
        },
        "یازدهم": {
            "ریاضی": ["شیمی", "فیزیک"],
            "تجربی": ["شیمی", "ریاضی", "فیزیک", "زیست"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی"],
            "تجربی": ["زیست", "فیزیک", "شیمی"]
        },
        "جامع": {
            "ریاضی": ["شیمی جلد 1 و 2", "گسسته", "هندسه", "حسابان", "فیزیک"],
            "تجربی": ["فیزیک", "ریاضی جلد ۱ و ۲", "زیست جلد ۱ و ۲ و ۳", "شیمی جلد ۱ و ۲"]
        }
    },
    "نشر الگو": {
        "دهم": {
            "ریاضی": ["فیزیک", "ریاضی"],
            "تجربی": ["فیزیک", "ریاضی", "زیست"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال"],
            "تجربی": ["فیزیک", "ریاضی", "زیست"]
        },
        "دوازدهم": {
            "ریاضی": ["گسسته", "فیزیک", "هندسه", "شیمی", "حسابان"],
            "تجربی": ["شیمی", "ریاضی", "فیزیک", "زیست"]
        },
        "جامع": {
            "ریاضی": ["فیزیک", "شیمی"],
            "تجربی": ["فیزیک", "شیمی"]
        }
    },
    "خیلی سبز": {
        "دهم": {
            "ریاضی": ["شیمی", "فیزیک", "ریاضی", "هندسه"],
            "تجربی": ["زیست", "شیمی", "فیزیک", "ریاضی"]
        },
        "یازدهم": {
            "ریاضی": ["شیمی", "فیزیک", "حسابان", "هندسه"],
            "تجربی": ["زیست", "شیمی", "فیزیک", "ریاضی"]
        },
        "دوازدهم": {
            "ریاضی": ["شیمی", "فیزیک", "حسابان", "گسسته", "هندسه"],
            "تجربی": ["زیست", "شیمی", "فیزیک", "ریاضی"]
        },
        "جامع": {
            "ریاضی": ["شیمی جلد ۱ و ۲", "فیزیک", "حسابان جلد ۱ و ۲", "گسسته", "هندسه جلد ۱ و ۲"],
            "تجربی": ["شیمی جلد ۱ و ۲", "فیزیک", "ریاضی جلد ۱ و ۲", "زیست جلد ۱ و ۲"]
        }
    },
    "نردبام": {
        "دهم": {
            "ریاضی": ["ریاضی", "فیزیک", "هندسه"],
            "تجربی": ["ریاضی", "زیست", "فیزیک"]
        },
        "یازدهم": {
            "ریاضی": ["شیمی", "فیزیک", "حسابان", "هندسه"],
            "تجربی": ["شیمی", "فیزیک", "زیست", "ریاضی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه"],
            "تجربی": ["فیزیک", "شیمی", "زیست"]
        },
        "جامع": {
            "ریاضی": ["شیمی", "حسابان", "فیزیک"],
            "تجربی": ["شیمی", "فیزیک", "ریاضی"]
        }
    }
}

# ========== لیست پایه‌های کتاب (با جامع) ==========
book_grades = ["دهم", "یازدهم", "دوازدهم", "جامع"]


async def book_grade_keyboard():
    """کیبورد پایه‌های کتاب با جامع"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
    kb.row(KeyboardButton("دوازدهم"), KeyboardButton("جامع"))
    kb.add(KeyboardButton("🔙 برگشت به منو"))
    return kb


async def book_publisher_keyboard(grade, major):
    """نمایش ناشرهای کتاب بر اساس پایه و رشته"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    
    added = set()
    for publisher, grades in book_subjects.items():
        if grade in grades and major in grades[grade]:
            kb.add(KeyboardButton(publisher))
            added.add(publisher)
    
    if not added:
        for publisher in book_subjects.keys():
            kb.add(KeyboardButton(publisher))
    
    kb.add(KeyboardButton("🔙 برگشت به منو"))
    return kb

async def book_subject_keyboard(publisher, grade, major):
    """نمایش دروس یک ناشر بر اساس پایه و رشته"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    
    subjects_list = book_subjects.get(publisher, {}).get(grade, {}).get(major, [])
    
    if subjects_list:
        for subject in subjects_list:
            kb.add(KeyboardButton(subject))
    else:
        kb.add(KeyboardButton("❌ درسی یافت نشد"))
    
    kb.add(KeyboardButton("🔙 برگشت به منو"))
    return kb
