from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.core import get_db
from database.models import Teacher, Publisher
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

def institute_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("ماز")
    kb.add("آلفا اسکول")
    kb.add("تایتان")
    kb.add("کلاسینو")
    return kb

def publisher_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("خیلی سبز")
    kb.add("نشر الگو")
    kb.add("گاج")
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
    "نشر الگو": {
        "دهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "ریاضی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "فیزیک", "شیمی", "هندسه"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "آمار و احتمال", "گسسته"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        }
    },
    "خیلی سبز": {
        "دهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "ریاضی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "فیزیک", "شیمی", "هندسه"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "آمار و احتمال", "گسسته"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        }
    },
    "نردبام": {
        "دهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "ریاضی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "فیزیک", "شیمی", "هندسه"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "آمار و احتمال", "گسسته"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        }
    },
    "فرمول بیست": {
        "دهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "ریاضی", "ادبیات", "دینی", "عربی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی", "ادبیات", "دینی", "عربی"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "فیزیک", "شیمی", "هندسه", "ادبیات", "دینی", "عربی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی", "ادبیات", "دینی", "عربی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "آمار و احتمال", "گسسته", "ادبیات", "دینی", "عربی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی", "ادبیات", "دینی", "عربی"]
        }
    },
    "IQ": {
        "دهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "ریاضی"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "یازدهم": {
            "ریاضی": ["حسابان", "آمار و احتمال", "فیزیک", "شیمی", "هندسه"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        },
        "دوازدهم": {
            "ریاضی": ["فیزیک", "شیمی", "هندسه", "حسابان", "آمار و احتمال", "گسسته"],
            "تجربی": ["فیزیک", "شیمی", "ریاضی", "زیست شناسی"]
        }
    }
}

def book_subject_keyboard(publisher, grade, major):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    books = book_subjects.get(publisher, {}).get(grade, {}).get(major, [])
    for book in books:
        kb.add(KeyboardButton(book))
    return kb

def book_publisher_keyboard(grade, major):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("نشر الگو")
    kb.add("خیلی سبز")
    kb.add("نردبام")
    kb.add("فرمول بیست")
    kb.add("IQ")
    return kb

# ========== دبیران (از دیتابیس) ==========
async def teacher_keyboard(grade, major, institute, subject):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # استانداردسازی نام درس‌ها
    subject_map = {
        "زیست": "زیست شناسی",
        "علوم و فنون": "علوم و فنون ادبی",
        "روانشناسی": "روان شناسی",
        "دینی": "دین و زندگی",
        "ادبیات": "فارسی",
    }
    subject = subject_map.get(subject, subject)
    
    async for db in get_db():
        # پیدا کردن publisher
        pub_result = await db.execute(select(Publisher).where(Publisher.name == institute))
        publisher = pub_result.scalar_one_or_none()
        
        if not publisher:
            return None
        
        # پیدا کردن دبیرها
        result = await db.execute(
            select(Teacher).where(
                Teacher.publisher_id == publisher.id,
                Teacher.grade == grade,
                Teacher.major == major,
                Teacher.subject == subject
            )
        )
        teachers = result.scalars().all()
    
    if not teachers:
        return None
    
    for t in teachers:
        kb.add(KeyboardButton(t.name))
    
    return kb
