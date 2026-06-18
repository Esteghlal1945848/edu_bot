from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

class Keyboards:
    @staticmethod
    def main_menu():
        builder = ReplyKeyboardBuilder()
        builder.add(
            KeyboardButton(text="📚 جستجوی جزوه"),
            KeyboardButton(text="🎥 جستجوی ویدئوهای درسی"),
            KeyboardButton(text="👨‍🏫 جستجوی دبیر"),
            KeyboardButton(text="⭐ برترین دبیرها"),
            KeyboardButton(text="🔥 ترندهای آموزشی"),
            KeyboardButton(text="⚙️ حساب کاربری")
        )
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def content_type_menu():
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📚 جزوه", callback_data="content_type:pdf"),
            InlineKeyboardButton(text="🎥 ویدئو", callback_data="content_type:video")
        )
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def grade_menu():
        builder = InlineKeyboardBuilder()
        grades = [
            ("هفتم", "7"), ("هشتم", "8"), ("نهم", "9"),
            ("دهم", "10"), ("یازدهم", "11"), ("دوازدهم", "12")
        ]
        for text, data in grades:
            builder.add(InlineKeyboardButton(text=text, callback_data=f"grade:{data}"))
        builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:main"))
        builder.adjust(3)
        return builder.as_markup()
    
    @staticmethod
    def lesson_menu(grade: str):
        builder = InlineKeyboardBuilder()
        lessons = {
            "7": [("ریاضی", "math"), ("علوم", "science")],
            "8": [("ریاضی", "math"), ("علوم", "science")],
            "9": [("ریاضی", "math"), ("علوم", "science")],
            "10": [("ریاضی", "math"), ("فیزیک", "physics"), ("شیمی", "chemistry")],
            "11": [("ریاضی", "math"), ("فیزیک", "physics"), ("شیمی", "chemistry")],
            "12": [("ریاضی", "math"), ("فیزیک", "physics"), ("شیمی", "chemistry")],
        }
        for text, data in lessons.get(grade, []):
            builder.add(InlineKeyboardButton(text=text, callback_data=f"lesson:{data}"))
        builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:grades"))
        builder.adjust(3)
        return builder.as_markup()
    
    @staticmethod
    def admin_panel():
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📊 داشبورد", callback_data="admin:dashboard"),
            InlineKeyboardButton(text="📁 آپلود فایل", callback_data="admin:upload")
        )
        builder.add(
            InlineKeyboardButton(text="📝 مدیریت محتوا", callback_data="admin:content"),
            InlineKeyboardButton(text="📢 ارسال همگانی", callback_data="admin:broadcast")
        )
        builder.adjust(2)
        return builder.as_markup()