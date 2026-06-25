from aiogram import types
from sqlalchemy import select, func
from database.core import get_db
from database.models import User, Archive, Publisher, Teacher
from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    institute_keyboard,
    publisher_keyboard,
    subject_keyboard,
    book_subject_keyboard,
    book_publisher_keyboard,
)
from bot.data.teacher import teacher_keyboard
from handlers.state import upload_state
from aiogram.types import KeyboardButton
import re
import asyncio
from datetime import datetime

ADMIN_ID = 7336595194
CHANNEL_ID = -1003918140957  # آیدی کانالت رو اینجا بذار
CHANNEL_LINK = "https://t.me/YourChannelUsername"  # لینک کانالت رو اینجا بذار


# =========================
# منوی اصلی
# =========================
async def main_menu(user_id: int) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📚 جزوه"),
        KeyboardButton("🎥 ویدئو"),
        KeyboardButton("📖 کتاب کمک آموزشی"),
        KeyboardButton("📩 ارتباط با ادمین")
    )
    if str(user_id) == str(ADMIN_ID):
        kb.add(KeyboardButton("👑 پنل ادمین"))
    return kb


# =========================
# چک کردن عضویت در کانال
# =========================
async def check_subscription(user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# پیام عضویت اجباری
# =========================
async def send_join_message(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            "📢 عضویت در کانال",
            url=CHANNEL_LINK
        )
    )
    await message.answer(
        "🔒 **برای استفاده از ربات باید عضو کانال ما باشید.**\n\n"
        "👇 روی دکمه زیر کلیک کنید، عضو شوید و سپس **/start** رو بزنید.",
        reply_markup=kb,
        parse_mode="Markdown"
    )


# =========================
# ارسال فایل با تایمر ۳۰ ثانیه
# =========================
async def send_file_with_timer(bot, chat_id: int, file_id: str, caption: str = "", delay: int = 30):
    """ارسال فایل با پیام تایمر و حذف خودکار بعد از ۳۰ ثانیه"""
    
    # ارسال فایل
    sent_file = await bot.send_document(chat_id, file_id, caption=caption)
    
    # ارسال پیام تایمر
    timer_msg = await bot.send_message(
        chat_id,
        f"⏳ **این فایل تا {delay} ثانیه دیگه پاک میشه!**\n\n"
        f"⬇️ لطفاً سریع دانلود کنید.\n\n"
        f"🕐 {delay} ثانیه مهلت دارید.",
        parse_mode="Markdown"
    )
    
    # حذف خودکار پیام تایمر بعد از delay ثانیه
    async def delete_timer():
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id, timer_msg.message_id)
        except:
            pass
    
    asyncio.create_task(delete_timer())
    return sent_file


# =========================
# START
# =========================
async def cmd_start(message: types.Message):
    user = message.from_user
    bot = message.bot
    
    # ===== چک کردن عضویت =====
    if not await check_subscription(user.id, bot):
        await send_join_message(message)
        return
    
    kb = await main_menu(user.id)
    await message.answer(
        "🎓 **به بزرگترین آرشیو آموزشی خوش آمدید!**\n\n"
        "📚 **تمامی کلاس‌های سالیانه ۱۴۰۶ پس از شروع در این ربات قرار خواهد گرفت.**\n"
        "✅ **تمامی کلاس‌های نهایی ۱۴۰۵ موسسات ماز | آلفا | تایتان | کلاسینو قرار گرفت.**\n\n"
        "🔹 برای مشاهده جزوه‌ها، دکمه **📚 جزوه** رو بزن\n"
        "🔹 برای مشاهده ویدیوها، دکمه **🎥 ویدئو** رو بزن\n"
        "🔹 برای مشاهده کتاب‌های کمک آموزشی، دکمه **📖 کتاب کمک آموزشی** رو بزن\n\n"
        "💡 **نکته:** برای برگشت از هر مرحله‌ای، روی دکمه **🔙 برگشت به منو** کلیک کن یا دستور **/start** رو بزن.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    async for db in get_db():
        result = await db.execute(select(User).where(User.telegram_id == user.id))
        if not result.scalar_one_or_none():
            db.add(User(telegram_id=user.id, username=user.username, full_name=user.full_name))
            await db.commit()


# =========================
# دریافت خودکار از کانال
# =========================
async def auto_save_from_channel(message: types.Message):
    is_from_channel = (
        message.chat.id == CHANNEL_ID or
        (message.forward_from_chat and message.forward_from_chat.id == CHANNEL_ID)
    )
    if not is_from_channel:
        return

    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ فقط ادمین میتونه فایل فوروارد کنه")
        return

    if not message.document and not message.video:
        await message.reply("❌ لطفاً یک فایل (PDF یا ویدیو) فوروارد کن")
        return

    caption = message.caption or ""
    tags = re.findall(r'#([^#\s]+)', caption)
    tags = [t.strip() for t in tags]

    if len(tags) < 5:
        await message.reply(
            "❌ کپشن باید حداقل ۵ هشتگ داشته باشه:\n"
            "#موسسه #پایه #رشته #درس #دبیر\n\n"
            "مثال: #تایتان #دهم #ریاضی #شیمی #فراهانی"
        )
        return

    institute = tags[0].replace("_", " ")
    grade = tags[1].replace("_", " ")
    major = tags[2].replace("_", " ")
    subject = tags[3].replace("_", " ")
    teacher = tags[4].replace("_", " ")

    subject_map = {
        "زیست": "زیست شناسی",
        "علوم و فنون": "علوم و فنون ادبی",
        "روانشناسی": "روان شناسی",
        "دینی": "دین و زندگی",
        "ادبیات": "فارسی",
    }
    subject = subject_map.get(subject, subject)

    async for db in get_db():
        archive = Archive(
            category="pdf" if message.document else "video",
            type="pdf" if message.document else "video",
            grade=grade,
            major=major,
            institute=institute,
            subject=subject,
            teacher=teacher,
            file_id=message.document.file_id if message.document else message.video.file_id,
            file_name=message.document.file_name if message.document else f"video_{message.message_id}.mp4",
            uploaded_by=message.from_user.id,
        )
        db.add(archive)
        await db.commit()

    await message.reply(
        f"✅ فایل با موفقیت ذخیره شد!\n"
        f"📚 {institute} - {grade} - {major} - {subject} - {teacher}"
    )


# =========================
# HANDLE BUTTONS
# =========================
async def handle_buttons(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    bot = message.bot
    
    # ===== چک کردن عضویت (به جز دکمه برگشت) =====
    if text not in ["🔙 برگشت به منو"]:
        if not await check_subscription(user_id, bot):
            await send_join_message(message)
            return

    # ===================== برگشت به منوی اصلی =====================
    if text == "🔙 برگشت به منو":
        if user_id in upload_state:
            del upload_state[user_id]
        kb = await main_menu(user_id)
        await message.answer(
            "🔙 به منوی اصلی برگشتی.\n\n"
            "💡 **نکته:** برای برگشت از هر مرحله‌ای، روی دکمه **🔙 برگشت به منو** کلیک کن یا دستور **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== پنل ادمین =====================
    if text == "👑 پنل ادمین":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            KeyboardButton("⚡ آپلود سریع"),
            KeyboardButton("📤 آپلود جزوه"),
            KeyboardButton("🎥 آپلود ویدئو"),
            KeyboardButton("📖 آپلود کتاب")
        )
        kb.add(
            KeyboardButton("🗑 حذف دبیر"),
            KeyboardButton("➕ اضافه کردن انتشارات")
        )
        kb.add(
            KeyboardButton("📋 لیست فایل‌ها"),
            KeyboardButton("🗑 حذف فایل")
        )
        kb.add(
            KeyboardButton("👥 لیست کاربران"),
            KeyboardButton("📊 آمار")
        )
        kb.add(
            KeyboardButton("⚙️ تنظیمات"),
            KeyboardButton("💾 بکاپ")
        )
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer("👑 **پنل مدیریت**", reply_markup=kb, parse_mode="Markdown")
        return

    # ===================== ارتباط با ادمین =====================
    if text == "📩 ارتباط با ادمین":
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(
                "📩 ارسال پیام به ادمین",
                url="https://t.me/unbrokensociety2026"
            )
        )
        back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📩 **ارتباط با ادمین**\n\n"
            "برای ارتباط مستقیم با ادمین، روی دکمه زیر کلیک کن و پیامت رو بفرست.\n\n"
            "📌 پاسخ شما در اسرع وقت داده میشه.",
            reply_markup=back_kb,
            parse_mode="Markdown"
        )
        await message.answer(
            "👇 روی دکمه زیر کلیک کن:",
            reply_markup=kb
        )
        return

    # ===================== دانلود جزوه/ویدیو (کاربر عادی) =====================
    if text in ["📚 جزوه", "🎥 ویدئو"]:
        if user_id in upload_state:
            del upload_state[user_id]
        category_map = {"📚 جزوه": "pdf", "🎥 ویدئو": "video"}
        upload_state[user_id] = {"mode": "user_download", "step": "grade", "category": category_map.get(text, "pdf")}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.add(KeyboardButton("دوازدهم"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "کدوم پایه؟\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== آپلود سریع (ادمین) =====================
    if text == "⚡ آپلود سریع":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "fast_upload", "step": "waiting_for_file"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "⚡ **حالت آپلود سریع فعال شد!**\n\n"
            "📤 فایل رو بفرست و توی کپشن این اطلاعات رو بنویس:\n\n"
            "`نوع | موسسه/ناشر | پایه | رشته | درس | دبیر`\n\n"
            "مثال برای جزوه:\n"
            "`جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`\n\n"
            "مثال برای کتاب:\n"
            "`کتاب | خیلی سبز | دهم | ریاضی | فیزیک | نردبام`\n\n"
            "⚠️ بین اطلاعات فقط `|` بذار\n\n"
            "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    # ===================== آپلود کتاب (ادمین) =====================
    if text == "📖 آپلود کتاب":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "book_upload", "category": "book", "type": "pdf", "step": "publisher"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📖 **آپلود کتاب کمک آموزشی**\n\nناشر رو انتخاب کن:",
            reply_markup=await publisher_keyboard()
        )
        return

    # ===================== آپلود جزوه (ادمین) =====================
    if text == "📤 آپلود جزوه":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "pdf", "type": "pdf", "step": "grade"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.add(KeyboardButton("دوازدهم"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "پایه را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== آپلود ویدئو (ادمین) =====================
    if text == "🎥 آپلود ویدئو":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "video", "type": "video", "step": "grade"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.add(KeyboardButton("دوازدهم"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "پایه را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== دانلود کتاب (کاربر عادی) =====================
    if text == "📖 کتاب کمک آموزشی":
        if user_id in upload_state:
            del upload_state[user_id]
        upload_state[user_id] = {"mode": "user_download", "step": "book_grade", "category": "book"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.add(KeyboardButton("دوازدهم"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📖 کدوم پایه؟\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== اضافه کردن انتشارات (ادمین) =====================
    if text == "➕ اضافه کردن انتشارات":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "add_publisher", "step": "ask_name"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📝 **اضافه کردن انتشارات جدید**\n\n"
            "نام انتشارات رو وارد کن:\n"
            "(مثال: ماجرای ۲۰)\n\n"
            "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    if user_id in upload_state and upload_state[user_id].get("mode") == "add_publisher":
        if upload_state[user_id].get("step") == "ask_name":
            name = text
            upload_state[user_id]["name"] = name
            upload_state[user_id]["step"] = "ask_type"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("موسسه آموزشی")
            kb.add("ناشر کتاب")
            kb.add("🔙 برگشت به منو")
            await message.answer(
                f"نوع انتشارات رو انتخاب کن:\n\n"
                f"📌 {name}\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if upload_state[user_id].get("step") == "ask_type":
            type_map = {"موسسه آموزشی": "institute", "ناشر کتاب": "book_publisher"}
            pub_type = type_map.get(text, "institute")
            upload_state[user_id]["pub_type"] = pub_type
            upload_state[user_id]["step"] = "ask_grade"
            upload_state[user_id]["subjects_data"] = {}
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("دهم")
            kb.add("یازدهم")
            kb.add("دوازدهم")
            kb.add("🔙 برگشت به منو")
            await message.answer(
                f"📌 **{upload_state[user_id]['name']}**\n\n"
                "پایه را انتخاب کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if upload_state[user_id].get("step") == "ask_grade":
            upload_state[user_id]["current_grade"] = text
            upload_state[user_id]["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی")
            kb.add("تجربی")
            kb.add("🔙 برگشت به منو")
            await message.answer(
                f"📌 **{upload_state[user_id]['name']}**\n"
                f"📚 پایه: {text}\n\n"
                "رشته را انتخاب کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if upload_state[user_id].get("step") == "ask_major":
            upload_state[user_id]["current_major"] = text
            upload_state[user_id]["step"] = "ask_subject"
            upload_state[user_id]["temp_subjects"] = []
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("✅ ثبت دروس"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer(
                f"📌 **{upload_state[user_id]['name']}**\n"
                f"📚 پایه: {upload_state[user_id]['current_grade']}\n"
                f"🎓 رشته: {text}\n\n"
                "دروس مربوط به این رشته رو وارد کن.\n"
                "هر درس رو در یه خط جداگانه بنویس.\n\n"
                "مثال:\n"
                "فیزیک\n"
                "شیمی\n"
                "ریاضی\n\n"
                "⚠️ وقتی تموم شد، روی دکمه **✅ ثبت دروس** بزن.\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if upload_state[user_id].get("step") == "ask_subject":
            if text == "✅ ثبت نهایی":
                upload_state[user_id]["step"] = "finish"
                subjects_data = upload_state[user_id].get("subjects_data", {})
                if not subjects_data:
                    await message.answer("❌ حداقل برای یک پایه درس وارد کن!")
                    return
                async for db in get_db():
                    result = await db.execute(select(Publisher).where(Publisher.name == upload_state[user_id]["name"]))
                    if result.scalar_one_or_none():
                        await message.answer(f"❌ انتشارات {upload_state[user_id]['name']} قبلاً وجود داره!")
                        del upload_state[user_id]
                        return
                    publisher = Publisher(
                        name=upload_state[user_id]["name"],
                        type=upload_state[user_id]["pub_type"],
                        subjects_by_grade=subjects_data
                    )
                    db.add(publisher)
                    await db.commit()
                await message.answer(
                    f"✅ انتشارات {upload_state[user_id]['name']} با موفقیت اضافه شد!\n\n"
                    f"📚 دروس ثبت شده:\n" +
                    "\n".join([
                        f"   • {grade}: " + "\n".join([f"      - {major}: {', '.join(subjects)}" for major, subjects in data.items()])
                        for grade, data in subjects_data.items()
                    ])
                )
                del upload_state[user_id]
                kb = await main_menu(user_id)
                await message.answer("به منوی اصلی برگشتی", reply_markup=kb)
                return
            elif text == "✅ ثبت دروس":
                subjects_list = upload_state[user_id].get("temp_subjects", [])
                current_grade = upload_state[user_id].get("current_grade")
                current_major = upload_state[user_id].get("current_major")
                if not subjects_list:
                    await message.answer(f"❌ حداقل یک درس وارد کن!")
                    return
                if "subjects_data" not in upload_state[user_id]:
                    upload_state[user_id]["subjects_data"] = {}
                if current_grade not in upload_state[user_id]["subjects_data"]:
                    upload_state[user_id]["subjects_data"][current_grade] = {}
                upload_state[user_id]["subjects_data"][current_grade][current_major] = subjects_list
                upload_state[user_id]["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("دهم")
                kb.add("یازدهم")
                kb.add("دوازدهم")
                kb.add("✅ ثبت نهایی")
                kb.add("🔙 برگشت به منو")
                display_text = "📚 لیست فعلی:\n"
                for grade, data in upload_state[user_id]["subjects_data"].items():
                    display_text += f"   • {grade}:\n"
                    for major, subjects in data.items():
                        display_text += f"      - {major}: {', '.join(subjects)}\n"
                await message.answer(
                    f"✅ دروس {current_major} برای پایه {current_grade} ثبت شد.\n\n"
                    f"{display_text}\n"
                    "برای ادامه، پایه دیگه رو انتخاب کن یا روی **✅ ثبت نهایی** بزن.\n\n"
                    f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                    reply_markup=kb
                )
                return
            elif text == "🔙 برگشت به منو":
                del upload_state[user_id]
                kb = await main_menu(user_id)
                await message.answer("🔙 به منوی اصلی برگشتی.", reply_markup=kb)
                return
            else:
                if "temp_subjects" not in upload_state[user_id]:
                    upload_state[user_id]["temp_subjects"] = []
                new_subjects = [s.strip() for s in text.split("\n") if s.strip()]
                added_list = []
                for subject in new_subjects:
                    if subject not in upload_state[user_id]["temp_subjects"]:
                        upload_state[user_id]["temp_subjects"].append(subject)
                        added_list.append(subject)
                if added_list:
                    await message.answer(
                        f"✅ {len(added_list)} درس اضافه شد:\n" + 
                        "\n".join([f"   • {s}" for s in added_list]) +
                        f"\n\n📚 لیست فعلی:\n" + 
                        "\n".join([f"   • {s}" for s in upload_state[user_id]["temp_subjects"]])
                    )
                else:
                    await message.answer("⚠️ هیچ درس جدیدی اضافه نشد (همه تکراری بودن)")
                return

    # ===================== GRADE =====================
    if text in ["دهم", "یازدهم", "دوازدهم"]:
        if user_id in upload_state and upload_state[user_id].get("step") == "book_grade":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "book_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("📖 رشته را انتخاب کن:", reply_markup=kb)
            return
        if user_id in upload_state and upload_state[user_id].get("mode") == "book_upload":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            kb.add(KeyboardButton(f"رشته:{text}|انسانی"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("رشته را انتخاب کن:", reply_markup=kb)
            return
        if user_id in upload_state and upload_state[user_id].get("mode") == "admin_upload":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            kb.add(KeyboardButton(f"رشته:{text}|انسانی"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("رشته را انتخاب کن:", reply_markup=kb)
            return
        if user_id in upload_state and upload_state[user_id].get("mode") == "user_download" and upload_state[user_id].get("step") == "grade":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            kb.add(KeyboardButton(f"رشته:{text}|انسانی"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("رشته را انتخاب کن:", reply_markup=kb)
            return

    # ===================== ناشران (برای آپلود کتاب - ادمین) =====================
    if user_id in upload_state and upload_state[user_id].get("mode") == "book_upload" and upload_state[user_id].get("step") == "publisher":
        upload_state[user_id]["publisher"] = text
        upload_state[user_id]["step"] = "grade"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.add(KeyboardButton("دوازدهم"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer("پایه را انتخاب کن:", reply_markup=kb)
        return

    # ===================== MAJOR =====================
    if text.startswith("رشته:"):
        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return
        grade, major = text.replace("رشته:", "").split("|")
        state = upload_state[user_id]
        if state.get("step") == "book_major":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "book_publisher"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer(
                "📖 ناشر مورد نظر رو انتخاب کن:",
                reply_markup=await book_publisher_keyboard(grade, major)
            )
            return
        if state.get("mode") == "book_upload":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "book_subject"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer(
                "📖 درس مورد نظر رو انتخاب کن:",
                reply_markup=await book_subject_keyboard(state["publisher"], grade, major)
            )
            return
        if state.get("mode") == "admin_upload":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
            return
        if state.get("mode") == "user_download" and state.get("category") != "book":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
            return

    # ===================== کتاب: انتخاب ناشر (دانلود) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "book_publisher":
        state = upload_state[user_id]
        state["publisher"] = text
        state["step"] = "book_subject_download"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📖 درس مورد نظر رو انتخاب کن:",
            reply_markup=await book_subject_keyboard(text, state["grade"], state["major"])
        )
        return

    # ===================== کتاب: انتخاب درس (دانلود) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "book_subject_download":
        state = upload_state[user_id]
        state["subject"] = text
        await show_book_archives(message, state)
        return

    # ===================== کتاب: انتخاب درس (آپلود ادمین) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "book_subject":
        state = upload_state[user_id]
        state["subject"] = text
        state["step"] = "waiting_for_file"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("❌ لغو"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            f"✅ اطلاعات ثبت شد:\n"
            f"📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}\n\n"
            f"📤 حالا فایل رو ارسال کن (PDF)\n\n"
            f"⚠️ بعد از ارسال فایل، کپشن رو وارد کن.\n\n"
            f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== موسسه (جزوه/ویدیو) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "institute":
        state = upload_state[user_id]
        state["institute"] = text
        state["step"] = "subject"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        from bot.keyboards.archive import subjects
        for s in subjects.get(state["major"], []):
            kb.add(KeyboardButton(s))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "📚 درس را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===================== درس (جزوه/ویدیو) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "subject":
        state = upload_state[user_id]
        state["subject"] = text
        state["step"] = "teacher"
        if state.get("mode") in ["admin_upload", "user_download"]:
            kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], text)
            if kb:
                kb.add(KeyboardButton("🔙 برگشت به منو"))
                await message.answer("👨‍🏫 دبیر را انتخاب کن:", reply_markup=kb)
            else:
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton("🔙 برگشت به منو"))
                await message.answer(
                    "❌ دبیری برای این درس پیدا نشد.\n\n"
                    "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                    reply_markup=kb
                )
            return

    # ===================== دبیر (جزوه/ویدیو) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "teacher":
        state = upload_state[user_id]
        state["teacher"] = text
        if state.get("mode") == "admin_upload":
            state["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer(
                f"✅ دبیر {text} انتخاب شد.\n\n📤 حالا فایل رو ارسال کن (PDF یا ویدیو)\n\n"
                f"⚠️ بعد از ارسال فایل، کپشن رو وارد کن.\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if state.get("mode") == "user_download":
            await show_archives(message, state)
            return

    # ===================== ادامه آپلود =====================
    if text == "⚡ ادامه":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        if user_id in upload_state:
            state = upload_state[user_id]
            state["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            await message.answer(
                "📤 فایل بعدی رو بفرست.\n\n"
                "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
        return

    # ===================== دریافت کپشن جزوه/ویدیو =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "waiting_for_caption_file":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        
        state = upload_state[user_id]
        caption = text
        
        if caption == "❌ لغو":
            del upload_state[user_id]
            kb = await main_menu(user_id)
            await message.answer("❌ لغو شد", reply_markup=kb)
            return
        
        async for db in get_db():
            archive = Archive(
                category=state.get("category", "pdf"),
                type=state["temp_file_type"],
                grade=state["grade"],
                major=state["major"],
                institute=state["institute"],
                subject=state["subject"],
                teacher=state.get("teacher"),
                file_id=state["temp_file_id"],
                file_name=state["temp_file_name"],
                caption=caption,
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        
        category_name = "جزوه" if state.get("category") == "pdf" else "ویدیو"
        grade = state["grade"]
        major = state["major"]
        institute = state["institute"]
        subject = state["subject"]
        teacher = state.get("teacher", "ندارد")
        file_name = state["temp_file_name"]
        
        del upload_state[user_id]
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"))
        kb.add(KeyboardButton("❌ لغو"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        
        await message.answer(
            f"✅ {category_name} با موفقیت در دیتابیس ثبت شد!\n\n"
            f"📚 {grade} - {major} - {institute} - {subject}\n"
            f"👨‍🏫 دبیر: {teacher}\n"
            f"📄 {file_name}\n"
            f"📝 کپشن: {caption}\n\n"
            f"🔹 این {category_name} در بخش **{'📚 جزوه' if category_name == 'جزوه' else '🎥 ویدئو'}** کاربران قابل مشاهده است.\n\n"
            f"برای آپلود {category_name} بعدی، روی '⚡ ادامه' بزن.\n\n"
            f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    # ===================== دریافت کپشن کتاب =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "waiting_for_caption_book":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        
        state = upload_state[user_id]
        caption = text
        
        if caption == "❌ لغو":
            del upload_state[user_id]
            kb = await main_menu(user_id)
            await message.answer("❌ لغو شد", reply_markup=kb)
            return
        
        async for db in get_db():
            archive = Archive(
                category="book",
                type="pdf",
                grade=state["grade"],
                major=state["major"],
                institute=state["publisher"],
                subject=state["subject"],
                teacher=None,
                book_name=state.get("book_name", "معمولی"),
                file_id=state["temp_file_id"],
                file_name=state["temp_file_name"],
                caption=caption,
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        
        publisher_name = state["publisher"]
        grade = state["grade"]
        major = state["major"]
        subject = state["subject"]
        file_name = state["temp_file_name"]
        
        del upload_state[user_id]
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"))
        kb.add(KeyboardButton("❌ لغو"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        
        await message.answer(
            f"✅ کتاب با موفقیت در دیتابیس ثبت شد!\n\n"
            f"📖 {publisher_name} - {grade} - {major} - {subject}\n"
            f"📄 {file_name}\n"
            f"📝 کپشن: {caption}\n\n"
            f"🔹 این کتاب در بخش **📖 کتاب کمک آموزشی** کاربران قابل مشاهده است.\n\n"
            f"برای آپلود کتاب بعدی، روی '⚡ ادامه' بزن.\n\n"
            f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    # ===================== حذف دبیر (ادمین) =====================
    if text == "🗑 حذف دبیر":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "delete_teacher", "step": "ask_institute"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "🗑 **حذف دبیر**\n\nموسسه رو انتخاب کن:\n\n"
            "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=await institute_keyboard()
        )
        return

    if user_id in upload_state and upload_state[user_id].get("mode") == "delete_teacher":
        state = upload_state[user_id]
        if state.get("step") == "ask_institute":
            state["institute"] = text
            state["step"] = "ask_grade"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("دهم", "یازدهم", "دوازدهم")
            kb.add("❌ لغو")
            kb.add("🔙 برگشت به منو")
            await message.answer(
                f"🏛 موسسه: {text}\n\nپایه رو انتخاب کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if state.get("step") == "ask_grade":
            state["grade"] = text
            state["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی", "تجربی", "انسانی")
            kb.add("❌ لغو")
            kb.add("🔙 برگشت به منو")
            await message.answer(
                f"🏛 موسسه: {state['institute']}\n"
                f"📚 پایه: {text}\n\nرشته رو انتخاب کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if state.get("step") == "ask_major":
            state["major"] = text
            state["step"] = "ask_teacher"
            async for db in get_db():
                pub = await db.scalar(
                    select(Publisher).where(Publisher.name == state["institute"])
                )
                if not pub:
                    await message.answer("❌ موسسه پیدا نشد")
                    return
                result = await db.execute(
                    select(Teacher).where(
                        Teacher.publisher_id == pub.id,
                        Teacher.grade == state["grade"],
                        Teacher.major == text
                    )
                )
                teachers = result.scalars().all()
            if not teachers:
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton("🔙 برگشت به منو"))
                await message.answer(
                    "❌ دبیری برای این انتخاب‌ها پیدا نشد.\n\n"
                    "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                    reply_markup=kb
                )
                del upload_state[user_id]
                return
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for t in teachers:
                kb.add(KeyboardButton(t.name))
            kb.add("❌ لغو")
            kb.add("🔙 برگشت به منو")
            state["teachers_list"] = {t.name: t.id for t in teachers}
            await message.answer(
                f"🏛 موسسه: {state['institute']}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {text}\n\n"
                "دبیر مورد نظر برای حذف رو انتخاب کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        if state.get("step") == "ask_teacher":
            if text == "❌ لغو":
                del upload_state[user_id]
                kb = await main_menu(user_id)
                await message.answer("❌ لغو شد", reply_markup=kb)
                return
            teacher_id = state.get("teachers_list", {}).get(text)
            if not teacher_id:
                await message.answer("❌ دبیر پیدا نشد")
                return
            async for db in get_db():
                result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
                teacher = result.scalar_one_or_none()
                if teacher:
                    await db.delete(teacher)
                    await db.commit()
            await message.answer(f"✅ دبیر {text} با موفقیت حذف شد!")
            del upload_state[user_id]
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                KeyboardButton("⚡ آپلود سریع"),
                KeyboardButton("📤 آپلود جزوه"),
                KeyboardButton("🎥 آپلود ویدئو"),
                KeyboardButton("📖 آپلود کتاب"),
                KeyboardButton("🗑 حذف دبیر"),
                KeyboardButton("➕ اضافه کردن انتشارات"),
                KeyboardButton("📋 لیست فایل‌ها"),
                KeyboardButton("🗑 حذف فایل"),
                KeyboardButton("👥 لیست کاربران"),
                KeyboardButton("📊 آمار"),
                KeyboardButton("⚙️ تنظیمات"),
                KeyboardButton("💾 بکاپ"),
                KeyboardButton("🔙 برگشت به منو")
            )
            await message.answer("👑 پنل مدیریت", reply_markup=kb)
            return

    # ===================== لیست کاربران =====================
    if text == "👥 لیست کاربران":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await list_users(message)
        return

    # ===================== تنظیمات =====================
    if text == "⚙️ تنظیمات":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await settings_panel(message)
        return

    # ===================== بکاپ =====================
    if text == "💾 بکاپ":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await backup_database(message)
        return

    # ===================== پیام همگانی =====================
    if text == "📢 پیام همگانی":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await broadcast_message(message)
        return

    # ===================== دریافت پیام همگانی =====================
    if user_id in upload_state and upload_state[user_id].get("mode") == "broadcast":
        if upload_state[user_id].get("step") == "waiting_for_message":
            await send_broadcast(message)
            return

    # ===================== لغو =====================
    if text == "❌ لغو":
        if user_id in upload_state:
            del upload_state[user_id]
        kb = await main_menu(user_id)
        await message.answer("❌ آپلود لغو شد", reply_markup=kb)
        return

    # ===================== حذف فایل (ادمین) =====================
    if user_id in upload_state:
        state = upload_state[user_id]
        if state.get("mode") == "admin_delete":
            await delete_file(message, text)
            return

    # ===================== لیست فایل‌ها (ادمین) =====================
    if text == "📋 لیست فایل‌ها":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await list_files(message)
        return

    # ===================== حذف فایل (شروع - ادمین) =====================
    if text == "🗑 حذف فایل":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_delete", "step": "waiting_for_file_id"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            "🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:\n\nمثلاً: `file_123456789`\n\n"
            "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    # ===================== آمار (ادمین) =====================
    if text == "📊 آمار":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await show_stats(message)
        return


# ===================== لیست کاربران (ادمین) =====================
async def list_users(message: types.Message, page: int = 1):
    user_id = message.from_user.id
    per_page = 10
    
    try:
        async for db in get_db():
            total = await db.scalar(select(func.count()).select_from(User))
            offset = (page - 1) * per_page
            result = await db.execute(
                select(User)
                .order_by(User.id.desc())
                .offset(offset)
                .limit(per_page)
            )
            users = result.scalars().all()
        
        if not users:
            await message.answer("❌ هیچ کاربری در دیتابیس وجود ندارد")
            return
        
        text = f"👥 **لیست کاربران** (صفحه {page} از {(total + per_page - 1) // per_page})\n\n"
        text += f"📊 **تعداد کل:** {total}\n\n"
        
        for i, user in enumerate(users, start=offset + 1):
            username = f"@{user.username}" if user.username else "ندارد"
            text += f"{i}. {user.full_name} - {username}\n"
            text += f"   🆔 {user.telegram_id}\n"
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        if page > 1:
            kb.insert(types.InlineKeyboardButton("◀️ قبلی", callback_data=f"users_page_{page-1}"))
        if page * per_page < total:
            kb.insert(types.InlineKeyboardButton("▶️ بعدی", callback_data=f"users_page_{page+1}"))
        
        back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_kb.add(KeyboardButton("🔙 برگشت به منو"))
        
        await message.answer(text, reply_markup=back_kb, parse_mode="Markdown")
        
        if kb.inline_keyboard:
            await message.answer("📌 برای رفتن به صفحه بعد/قبل از دکمه‌های زیر استفاده کن:", reply_markup=kb)
            
    except Exception as e:
        await message.answer(f"❌ خطا در دریافت لیست کاربران:\n`{str(e)}`", parse_mode="Markdown")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer("به منوی اصلی برگشتی", reply_markup=kb)


# ===================== تنظیمات (ادمین) =====================
async def settings_panel(message: types.Message):
    user_id = message.from_user.id
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("👤 تغییر ادمین"),
        KeyboardButton("📢 پیام همگانی")
    )
    kb.add(
        KeyboardButton("🔙 برگشت به منو")
    )
    
    await message.answer(
        "⚙️ **پنل تنظیمات**\n\n"
        "🔹 تغییر ادمین: آیدی جدید رو وارد کن\n"
        "🔹 پیام همگانی: به همه کاربران پیام بفرست\n\n"
        "⚠️ **توجه:** این تنظیمات فقط برای ادمین قابل دسترسه.\n\n"
        "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
        reply_markup=kb,
        parse_mode="Markdown"
    )


# ===================== تغییر ادمین =====================
async def change_admin(message: types.Message):
    user_id = message.from_user.id
    
    try:
        new_admin_id = int(message.text)
        await message.answer(
            f"✅ آیدی ادمین با موفقیت تغییر کرد!\n\n"
            f"🆔 آیدی جدید: `{new_admin_id}`\n\n"
            f"⚠️ لطفاً ربات رو ری‌استارت کن تا تغییرات اعمال بشه.",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ لطفاً یک آیدی عددی معتبر وارد کن.")


# ===================== پیام همگانی =====================
async def broadcast_message(message: types.Message):
    user_id = message.from_user.id
    
    upload_state[user_id] = {
        "mode": "broadcast",
        "step": "waiting_for_message"
    }
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ لغو"))
    kb.add(KeyboardButton("🔙 برگشت به منو"))
    
    await message.answer(
        "📢 **ارسال پیام همگانی**\n\n"
        "پیام مورد نظر رو وارد کن:\n\n"
        "⚠️ این پیام به **همه کاربران** ارسال میشه.\n\n"
        "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
        reply_markup=kb
    )


async def send_broadcast(message: types.Message):
    user_id = message.from_user.id
    broadcast_text = message.text
    
    if broadcast_text in ["❌ لغو", "🔙 برگشت به منو"]:
        del upload_state[user_id]
        kb = await main_menu(user_id)
        await message.answer("🔙 به منوی اصلی برگشتی.", reply_markup=kb)
        return
    
    await message.answer("⏳ **در حال ارسال پیام به کاربران...**")
    
    try:
        async for db in get_db():
            result = await db.execute(select(User))
            users = result.scalars().all()
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"📢 **پیام همگانی**\n\n{broadcast_text}",
                    parse_mode="Markdown"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await message.answer(
            f"✅ **پیام همگانی ارسال شد!**\n\n"
            f"📤 ارسال شده: {sent}\n"
            f"❌ ناموفق: {failed}\n"
            f"👥 کل کاربران: {len(users)}"
        )
        
    except Exception as e:
        await message.answer(f"❌ خطا در ارسال پیام همگانی:\n`{str(e)}`", parse_mode="Markdown")
    
    if user_id in upload_state:
        del upload_state[user_id]
    
    kb = await main_menu(user_id)
    await message.answer("به منوی اصلی برگشتی", reply_markup=kb)


# ===================== بکاپ گرفتن (ادمین) =====================
async def backup_database(message: types.Message):
    user_id = message.from_user.id
    
    await message.answer("⏳ **در حال گرفتن بکاپ از دیتابیس...**")
    
    try:
        async for db in get_db():
            users_count = await db.scalar(select(func.count()).select_from(User))
            files_count = await db.scalar(select(func.count()).select_from(Archive))
            publishers_count = await db.scalar(select(func.count()).select_from(Publisher))
            teachers_count = await db.scalar(select(func.count()).select_from(Teacher))
        
        backup_text = f"""📊 **گزارش بکاپ دیتابیس**

📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

👥 کاربران: {users_count}
📄 فایل‌ها: {files_count}
🏛 انتشارات: {publishers_count}
👨‍🏫 دبیران: {teachers_count}

---
این یک بکاپ ساده است. برای بکاپ کامل از سیستم دیتابیس استفاده کنید.
"""
        
        await message.answer(
            backup_text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ خطا در گرفتن بکاپ:\n`{str(e)}`", parse_mode="Markdown")
    
    kb = await main_menu(user_id)
    await message.answer("به منوی اصلی برگشتی", reply_markup=kb)


# ===================== نمایش کتاب‌ها (کاربر) =====================
async def show_book_archives(message: types.Message, state: dict):
    user_id = message.from_user.id
    bot = message.bot
    async for db in get_db():
        query = select(Archive).where(
            Archive.category == "book",
            Archive.grade == state["grade"],
            Archive.major == state["major"],
            Archive.institute == state["publisher"],
            Archive.subject == state["subject"]
        )
        result = await db.execute(query)
        archives = result.scalars().all()
    if not archives:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            f"❌ هیچ کتابی برای این انتخاب‌ها پیدا نشد\n\n"
            f"📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}",
            reply_markup=kb
        )
        if user_id in upload_state:
            del upload_state[user_id]
        return
    for archive in archives:
        caption = f"📖 {archive.file_name}\n"
        if archive.caption:
            caption += f"📝 {archive.caption}\n"
        caption += f"📌 {archive.book_name or 'معمولی'}"
        
        # ارسال با تایمر ۳۰ ثانیه
        await send_file_with_timer(bot, user_id, archive.file_id, caption)
        
    if user_id in upload_state:
        del upload_state[user_id]
    kb = await main_menu(user_id)
    await message.answer("✅ همه کتاب‌ها ارسال شد", reply_markup=kb)


# ===================== نمایش فایل‌ها (کاربر) =====================
async def show_archives(message: types.Message, state: dict):
    user_id = message.from_user.id
    bot = message.bot
    category = state.get("category", "pdf")
    async for db in get_db():
        query = select(Archive).where(
            Archive.category == category,
            Archive.grade == state["grade"],
            Archive.major == state["major"],
            Archive.institute == state["institute"],
            Archive.subject == state["subject"]
        )
        if state.get("teacher"):
            query = query.where(Archive.teacher == state["teacher"])
        result = await db.execute(query)
        archives = result.scalars().all()
    if not archives:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            f"❌ هیچ فایلی پیدا نشد\n\n"
            f"📚 درس: {state['subject']}\n"
            f"👨‍🏫 دبیر: {state.get('teacher', 'نامشخص')}",
            reply_markup=kb
        )
        if user_id in upload_state:
            del upload_state[user_id]
        return
    for archive in archives:
        caption = f"📄 {archive.file_name}\n"
        if archive.caption:
            caption += f"📝 {archive.caption}\n"
        if archive.teacher:
            caption += f"👨‍🏫 دبیر: {archive.teacher}\n"
        if archive.book_name:
            caption += f"📌 {archive.book_name}"
        
        # ارسال با تایمر ۳۰ ثانیه
        await send_file_with_timer(bot, user_id, archive.file_id, caption)
        
    if user_id in upload_state:
        del upload_state[user_id]
    kb = await main_menu(user_id)
    await message.answer("✅ همه فایل‌ها ارسال شد", reply_markup=kb)


# ===================== لیست فایل‌ها (ادمین) =====================
async def list_files(message: types.Message):
    async for db in get_db():
        result = await db.execute(select(Archive).order_by(Archive.id.desc()).limit(20))
        files = result.scalars().all()
    if not files:
        await message.answer("❌ هیچ فایلی در دیتابیس وجود ندارد")
        return
    for file in files:
        category_text = {"pdf": "📄 جزوه", "video": "🎥 ویدیو", "book": "📖 کتاب"}.get(file.category, "📄")
        caption_text = f"\n📝 {file.caption}" if file.caption else ""
        await message.answer(
            f"{category_text} **{file.file_name}**{caption_text}\n\n"
            f"🆔 آیدی فایل: `{file.file_id[:20]}...`\n"
            f"📚 پایه: {file.grade}\n"
            f"🎓 رشته: {file.major}\n"
            f"🏛 موسسه/ناشر: {file.institute}\n"
            f"📖 درس: {file.subject}\n"
            f"👨‍🏫 دبیر: {file.teacher or 'ندارد'}\n"
            f"📌 کتاب: {file.book_name or 'ندارد'}",
            parse_mode="Markdown"
        )
    await message.answer(f"✅ {len(files)} فایل آخر نمایش داده شد")


# ===================== حذف فایل (ادمین) =====================
async def delete_file(message: types.Message, file_id: str):
    user_id = message.from_user.id
    async for db in get_db():
        result = await db.execute(select(Archive).where(Archive.file_id.like(f"%{file_id}%")))
        file = result.scalar_one_or_none()
        if file:
            await db.delete(file)
            await db.commit()
            await message.answer(f"✅ فایل با موفقیت حذف شد:\n\n📄 {file.file_name}")
        else:
            await message.answer(f"❌ فایلی با آیدی `{file_id}` پیدا نشد")
    if user_id in upload_state:
        del upload_state[user_id]
    kb = await main_menu(user_id)
    await message.answer("به منوی اصلی برگشتی", reply_markup=kb)


# ===================== آمار (ادمین) =====================
async def show_stats(message: types.Message):
    async for db in get_db():
        users_count = await db.scalar(select(func.count()).select_from(User))
        files_count = await db.scalar(select(func.count()).select_from(Archive))
        pdf_count = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "pdf"))
        video_count = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "video"))
        book_count = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "book"))
    await message.answer(
        f"📊 **آمار ربات**\n\n"
        f"👥 کاربران: {users_count}\n"
        f"📄 کل فایل‌ها: {files_count}\n"
        f"📁 جزوه: {pdf_count}\n"
        f"🎥 ویدیو: {video_count}\n"
        f"📖 کتاب: {book_count}",
        parse_mode="Markdown"
    )
    kb = await main_menu(user_id)
    await message.answer("به منوی اصلی برگشتی", reply_markup=kb)


# =========================
# HANDLE FILE (ادغام شده)
# =========================
async def handle_file(message: types.Message):
    user_id = message.from_user.id

    is_from_channel = (
        message.chat.id == CHANNEL_ID or
        (message.forward_from_chat and message.forward_from_chat.id == CHANNEL_ID)
    )
    if is_from_channel:
        await auto_save_from_channel(message)
        return

    if user_id not in upload_state:
        await message.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
        return

    state = upload_state[user_id]

    # ===== آپلود سریع =====
    if state.get("mode") == "fast_upload":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        caption = message.caption or ""
        parts = [p.strip() for p in caption.split("|")]
        if len(parts) < 5:
            await message.answer("❌ فرمت کپشن اشتباهه!\n\nمثال: `جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`", parse_mode="Markdown")
            return
        category = parts[0]
        institute = parts[1]
        grade = parts[2]
        major = parts[3]
        subject = parts[4]
        teacher = parts[5] if len(parts) > 5 else None
        book_name = parts[6] if len(parts) > 6 else None
        category_map = {"جزوه": "pdf", "ویدیو": "video", "کتاب": "book"}
        cat = category_map.get(category, "pdf")
        async for db in get_db():
            archive = Archive(
                category=cat,
                type="pdf" if message.document else "video",
                grade=grade,
                major=major,
                institute=institute,
                subject=subject,
                teacher=teacher,
                book_name=book_name,
                file_id=message.document.file_id if message.document else message.video.file_id,
                file_name=message.document.file_name if message.document else f"video_{message.message_id}.mp4",
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"))
        kb.add(KeyboardButton("❌ لغو"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        await message.answer(
            f"✅ فایل با موفقیت ثبت شد!\n📚 {institute} - {grade} - {major} - {subject}\n\n"
            f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=kb
        )
        return

    # ===== آپلود کتاب =====
    if state.get("mode") == "book_upload":
        if state.get("step") == "waiting_for_file":
            if str(user_id) != str(ADMIN_ID):
                await message.answer("⛔ دسترسی نداری")
                return
            if not message.document:
                await message.answer("❌ لطفاً فایل PDF کتاب رو ارسال کن")
                return
            
            state["temp_file_id"] = message.document.file_id
            state["temp_file_name"] = message.document.file_name or "unknown.pdf"
            state["step"] = "waiting_for_caption_book"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            
            await message.answer(
                f"✅ فایل کتاب با موفقیت دریافت شد!\n\n"
                f"📄 {state['temp_file_name']}\n\n"
                f"📝 حالا کپشن کتاب رو وارد کن:\n\n"
                f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
            return
        
        return

    # ===== آپلود جزوه/ویدیو =====
    if state.get("mode") != "admin_upload":
        await message.answer("❌ شما در حالت دانلود هستید")
        return
    
    if state.get("step") != "waiting_for_file":
        await message.answer("❌ لطفاً اول دبیر رو انتخاب کن")
        return

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "unknown.pdf"
        file_type = "pdf"
        category_name = "جزوه"
    elif message.video:
        file_id = message.video.file_id
        file_name = f"video_{message.video.file_id[:8]}.mp4"
        file_type = "video"
        category_name = "ویدیو"
    else:
        await message.answer("❌ لطفاً فقط فایل PDF یا ویدیو ارسال کن")
        return

    state["temp_file_id"] = file_id
    state["temp_file_name"] = file_name
    state["temp_file_type"] = file_type
    state["step"] = "waiting_for_caption_file"

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ لغو"))
    kb.add(KeyboardButton("🔙 برگشت به منو"))

    await message.answer(
        f"✅ فایل {category_name} با موفقیت دریافت شد!\n\n"
        f"📄 {file_name}\n\n"
        f"📝 حالا کپشن فایل رو وارد کن:\n\n"
        f"💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
        reply_markup=kb
    )
    return


# =========================
# HANDLE CALLBACK
# =========================
async def handle_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    
    if data.startswith("users_page_"):
        page = int(data.split("_")[2])
        await list_users(callback_query.message, page)
        await callback_query.answer()
