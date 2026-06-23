# handlers/start.py

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
    teacher_keyboard
)
from handlers.state import upload_state
from aiogram.types import KeyboardButton

ADMIN_ID = 7336595194

async def cmd_start(message: types.Message):
    user = message.from_user
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📚 جزوه"),
        KeyboardButton("🎥 ویدئو"),
        KeyboardButton("📖 کتاب کمک آموزشی"),
        KeyboardButton("📩 ارتباط با ادمین")
    )
    if str(user.id) == str(ADMIN_ID):
        kb.add(KeyboardButton("👑 پنل ادمین"))
    await message.answer(
        "🎓 **به بزرگترین آرشیو آموزشی خوش آمدید!**\n\n"
        "📚 **تمامی کلاس‌های سالیانه ۱۴۰۶ پس از شروع در این ربات قرار خواهد گرفت.**\n"
        "✅ **تمامی کلاس‌های نهایی ۱۴۰۵ موسسات ماز | آلفا | تایتان | کلاسینو قرار گرفت.**\n\n"
        "🔹 برای مشاهده جزوه‌ها، دکمه **📚 جزوه** رو بزن\n"
        "🔹 برای مشاهده ویدیوها، دکمه **🎥 ویدئو** رو بزن\n"
        "🔹 برای مشاهده کتاب‌های کمک آموزشی، دکمه **📖 کتاب کمک آموزشی** رو بزن",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    async for db in get_db():
        result = await db.execute(select(User).where(User.telegram_id == user.id))
        if not result.scalar_one_or_none():
            db.add(User(telegram_id=user.id, username=user.username, full_name=user.full_name))
            await db.commit()

async def handle_buttons(message: types.Message):
    text = message.text
    user_id = message.from_user.id

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
            KeyboardButton("📖 آپلود کتاب"),
            KeyboardButton("➕ اضافه کردن دبیر"),
            KeyboardButton("➕ اضافه کردن انتشارات"),
            KeyboardButton("📋 لیست فایل‌ها"),
            KeyboardButton("🗑 حذف فایل"),
            KeyboardButton("📊 آمار")
        )
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
        await message.answer(
            "📩 **ارتباط با ادمین**\n\n"
            "برای ارتباط مستقیم با ادمین، روی دکمه زیر کلیک کن و پیامت رو بفرست.\n\n"
            "📌 پاسخ شما در اسرع وقت داده میشه.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    # ===================== آپلود سریع =====================
    if text == "⚡ آپلود سریع":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "fast_upload", "step": "waiting_for_file"}
        await message.answer(
            "⚡ **حالت آپلود سریع فعال شد!**\n\n"
            "📤 فایل رو بفرست و توی کپشن این اطلاعات رو بنویس:\n\n"
            "`نوع | موسسه/ناشر | پایه | رشته | درس | دبیر`\n\n"
            "مثال برای جزوه:\n"
            "`جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`\n\n"
            "مثال برای کتاب:\n"
            "`کتاب | خیلی سبز | دهم | ریاضی | فیزیک | نردبام`\n\n"
            "⚠️ بین اطلاعات فقط `|` بذار",
            parse_mode="Markdown"
        )
        return

    # ===================== آپلود کتاب (ادمین) =====================
    if text == "📖 آپلود کتاب":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "book_upload", "category": "book", "type": "pdf", "step": "publisher"}
        await message.answer("📖 **آپلود کتاب کمک آموزشی**\n\nناشر رو انتخاب کن:", reply_markup=publisher_keyboard())
        return

    # ===================== آپلود جزوه =====================
    if text == "📤 آپلود جزوه":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "pdf", "type": "pdf", "step": "grade"}
        await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
        return

    # ===================== آپلود ویدئو =====================
    if text == "🎥 آپلود ویدئو":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "video", "type": "video", "step": "grade"}
        await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
        return

    # ===================== اضافه کردن انتشارات (ادمین) =====================
    if text == "➕ اضافه کردن انتشارات":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "add_publisher", "step": "ask_name"}
        await message.answer(
            "📝 **اضافه کردن انتشارات جدید**\n\n"
            "نام انتشارات رو وارد کن:\n"
            "(مثال: ماجرای ۲۰)"
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
            await message.answer(
                f"نوع انتشارات رو انتخاب کن:\n\n"
                f"📌 {name}",
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
            
            await message.answer(
                f"📌 **{upload_state[user_id]['name']}**\n\n"
                "پایه را انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if upload_state[user_id].get("step") == "ask_grade":
            upload_state[user_id]["current_grade"] = text
            upload_state[user_id]["step"] = "ask_major"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی")
            kb.add("تجربی")
            
            await message.answer(
                f"📌 **{upload_state[user_id]['name']}**\n"
                f"📚 پایه: {text}\n\n"
                "رشته را انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if upload_state[user_id].get("step") == "ask_major":
            upload_state[user_id]["current_major"] = text
            upload_state[user_id]["step"] = "ask_subject"
            upload_state[user_id]["temp_subjects"] = []
            
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
                "⚠️ وقتی تموم شد، روی دکمه **✅ ثبت دروس** بزن.",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                    KeyboardButton("✅ ثبت دروس"),
                    KeyboardButton("🔙 برگشت")
                )
            )
            return
        
        if upload_state[user_id].get("step") == "ask_subject":
            if text == "✅ ثبت دروس":
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
                kb.add("❌ لغو")
                
                await message.answer(
                    f"✅ دروس {current_major} برای پایه {current_grade} ثبت شد.\n\n"
                    f"📚 لیست فعلی:\n" +
                    "\n".join([
                        f"   • {grade}: " + "\n".join([f"      - {major}: {', '.join(subjects)}" for major, subjects in data.items()])
                        for grade, data in upload_state[user_id]["subjects_data"].items()
                    ]) +
                    "\n\nبرای ادامه، پایه دیگه رو انتخاب کن یا روی **✅ ثبت نهایی** بزن.",
                    reply_markup=kb
                )
                return
            
            elif text == "🔙 برگشت":
                upload_state[user_id]["step"] = "ask_grade"
                upload_state[user_id]["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("دهم")
                kb.add("یازدهم")
                kb.add("دوازدهم")
                await message.answer("🔙 برگشتی به انتخاب پایه.", reply_markup=kb)
                return
            
            elif text == "❌ لغو":
                del upload_state[user_id]
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(
                    KeyboardButton("⚡ آپلود سریع"),
                    KeyboardButton("📤 آپلود جزوه"),
                    KeyboardButton("🎥 آپلود ویدئو"),
                    KeyboardButton("📖 آپلود کتاب"),
                    KeyboardButton("➕ اضافه کردن دبیر"),
                    KeyboardButton("➕ اضافه کردن انتشارات"),
                    KeyboardButton("📋 لیست فایل‌ها"),
                    KeyboardButton("🗑 حذف فایل"),
                    KeyboardButton("📊 آمار")
                )
                await message.answer("❌ عملیات لغو شد", reply_markup=kb)
                return
            
            else:
                if "temp_subjects" not in upload_state[user_id]:
                    upload_state[user_id]["temp_subjects"] = []
                
                if text not in upload_state[user_id]["temp_subjects"]:
                    upload_state[user_id]["temp_subjects"].append(text)
                    await message.answer(
                        f"✅ درس {text} به لیست اضافه شد.\n\n"
                        f"📚 لیست فعلی:\n" + "\n".join([f"   • {s}" for s in upload_state[user_id]["temp_subjects"]])
                    )
                else:
                    await message.answer(f"⚠️ درس {text} قبلاً اضافه شده!")
                return
        
        # ثبت نهایی
        if upload_state[user_id].get("step") == "ask_grade" and text == "✅ ثبت نهایی":
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
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                KeyboardButton("⚡ آپلود سریع"),
                KeyboardButton("📤 آپلود جزوه"),
                KeyboardButton("🎥 آپلود ویدئو"),
                KeyboardButton("📖 آپلود کتاب"),
                KeyboardButton("➕ اضافه کردن دبیر"),
                KeyboardButton("➕ اضافه کردن انتشارات"),
                KeyboardButton("📋 لیست فایل‌ها"),
                KeyboardButton("🗑 حذف فایل"),
                KeyboardButton("📊 آمار")
            )
            await message.answer("👑 پنل مدیریت", reply_markup=kb)
            return

    # ===================== اضافه کردن دبیر (ادمین) =====================
    if text == "➕ اضافه کردن دبیر":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "add_teacher", "step": "ask_name"}
        await message.answer(
            "📝 **اضافه کردن دبیر جدید**\n\n"
            "نام کامل دبیر رو وارد کن:\n"
            "(مثال: محمدرضا شجاعی)"
        )
        return

    if user_id in upload_state and upload_state[user_id].get("mode") == "add_teacher":
        state = upload_state[user_id]
        
        if state.get("step") == "ask_name":
            state["name"] = text
            state["step"] = "ask_publisher"
            
            async for db in get_db():
                result = await db.execute(
                    select(Publisher).where(
                        Publisher.type == "institute"
                    )
                )
                publishers = result.scalars().all()
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for p in publishers:
                kb.add(p.name)
            kb.add("❌ لغو")
            
            await message.answer(
                f"📌 دبیر: {state['name']}\n\n"
                "موسسه مربوطه رو انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if state.get("step") == "ask_publisher":
            async for db in get_db():
                result = await db.execute(select(Publisher).where(Publisher.name == text))
                publisher = result.scalar_one_or_none()
                if not publisher:
                    await message.answer("❌ موسسه پیدا نشد. دوباره انتخاب کن.")
                    return
                state["publisher_id"] = publisher.id
                state["publisher_name"] = publisher.name
                state["step"] = "ask_grade"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("دهم", "یازدهم", "دوازدهم")
            await message.answer(
                f"📌 دبیر: {state['name']}\n"
                f"🏛 موسسه: {state['publisher_name']}\n\n"
                "پایه رو انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if state.get("step") == "ask_grade":
            state["grade"] = text
            state["step"] = "ask_major"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی", "تجربی", "انسانی")
            await message.answer(
                f"📌 دبیر: {state['name']}\n"
                f"🏛 موسسه: {state.get('publisher_name', '')}\n"
                f"📚 پایه: {text}\n\n"
                "رشته رو انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if state.get("step") == "ask_major":
            state["major"] = text
            state["step"] = "ask_subject"
            
            subjects = {
                "ریاضی": ["فیزیک", "شیمی", "ریاضی", "هندسه", "فارسی", "عربی", "حسابان", "گسسته", "آمار و احتمال"],
                "تجربی": ["زیست شناسی", "شیمی", "فیزیک", "ریاضی", "فارسی", "عربی"],
                "انسانی": ["علوم و فنون ادبی", "ریاضی و آمار", "جامعه شناسی", "منطق", "اقتصاد", "فارسی", 
                           "روان شناسی", "فلسفه", "عربی تخصصی", "دین و زندگی", "فلسفه و منطق", "تاریخ", "جغرافیا", "دینی"]
            }
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subjects.get(text, []):
                kb.add(s)
            kb.add("❌ لغو")
            
            await message.answer(
                f"📌 دبیر: {state['name']}\n"
                f"🏛 موسسه: {state.get('publisher_name', '')}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {text}\n\n"
                "درس رو انتخاب کن:",
                reply_markup=kb
            )
            return
        
        if state.get("step") == "ask_subject":
            if text == "❌ لغو":
                del upload_state[user_id]
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(
                    KeyboardButton("⚡ آپلود سریع"),
                    KeyboardButton("📤 آپلود جزوه"),
                    KeyboardButton("🎥 آپلود ویدئو"),
                    KeyboardButton("📖 آپلود کتاب"),
                    KeyboardButton("➕ اضافه کردن دبیر"),
                    KeyboardButton("➕ اضافه کردن انتشارات"),
                    KeyboardButton("📋 لیست فایل‌ها"),
                    KeyboardButton("🗑 حذف فایل"),
                    KeyboardButton("📊 آمار")
                )
                await message.answer("❌ عملیات لغو شد", reply_markup=kb)
                return
            
            state["subject"] = text
            
            async for db in get_db():
                teacher = Teacher(
                    name=state["name"],
                    publisher_id=state["publisher_id"],
                    grade=state["grade"],
                    major=state["major"],
                    subject=state["subject"]
                )
                db.add(teacher)
                await db.commit()
            
            await message.answer(
                f"✅ دبیر {state['name']} با موفقیت اضافه شد!\n\n"
                f"📚 {state['grade']} - {state['major']} - {state['subject']}\n"
                f"🏛 {state.get('publisher_name', '')}"
            )
            
            del upload_state[user_id]
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                KeyboardButton("⚡ آپلود سریع"),
                KeyboardButton("📤 آپلود جزوه"),
                KeyboardButton("🎥 آپلود ویدئو"),
                KeyboardButton("📖 آپلود کتاب"),
                KeyboardButton("➕ اضافه کردن دبیر"),
                KeyboardButton("➕ اضافه کردن انتشارات"),
                KeyboardButton("📋 لیست فایل‌ها"),
                KeyboardButton("🗑 حذف فایل"),
                KeyboardButton("📊 آمار")
            )
            await message.answer("👑 پنل مدیریت", reply_markup=kb)
            return

    # ===================== دانلود کتاب =====================
    if text == "📖 کتاب کمک آموزشی":
        if user_id in upload_state:
            del upload_state[user_id]
        upload_state[user_id] = {"mode": "user_download", "step": "book_grade", "category": "book"}
        await message.answer("📖 کدوم پایه؟", reply_markup=grade_keyboard())
        return

    # ===================== GRADE =====================
    if text in ["دهم", "یازدهم", "دوازدهم"]:
        
        if user_id in upload_state and upload_state[user_id].get("step") == "book_grade":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "book_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            await message.answer("📖 رشته را انتخاب کن:", reply_markup=kb)
            return

        if user_id in upload_state and upload_state[user_id].get("mode") == "book_upload":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"
            await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
            return

        if user_id in upload_state and upload_state[user_id].get("mode") == "admin_upload":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"
            await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
            return

        if user_id in upload_state:
            del upload_state[user_id]
        upload_state[user_id] = {"mode": "user_download", "step": "major", "grade": text}
        await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
        return

    # ===================== ناشران (برای آپلود کتاب - ادمین) =====================
    if text in ["خیلی سبز", "نشر الگو", "نردبام", "فرمول بیست", "IQ"]:
        if user_id in upload_state and upload_state[user_id].get("mode") == "book_upload":
            upload_state[user_id]["publisher"] = text
            upload_state[user_id]["step"] = "grade"
            await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
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
            await message.answer(
                "📖 ناشر مورد نظر رو انتخاب کن:",
                reply_markup=await book_publisher_keyboard(grade, major)
            )
            return

        if state.get("mode") == "book_upload":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "book_subject"
            await message.answer(
                "📖 درس مورد نظر رو انتخاب کن:",
                reply_markup=await book_subject_keyboard(state["publisher"], grade, major)
            )
            return

        if state.get("mode") == "admin_upload":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
            return

        if state.get("mode") == "user_download" and state.get("step") != "book_major":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
            return

    # ===================== کتاب: انتخاب ناشر (دانلود) =====================
    if text in ["نشر الگو", "خیلی سبز", "نردبام", "فرمول بیست", "IQ"]:
        if user_id in upload_state and upload_state[user_id].get("step") == "book_publisher":
            state = upload_state[user_id]
            state["publisher"] = text
            state["step"] = "book_subject_download"
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
        await message.answer(
            f"✅ اطلاعات ثبت شد:\n"
            f"📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}\n\n"
            f"📤 حالا فایل رو ارسال کن (PDF)",
            reply_markup=kb
        )
        return

    # ===================== موسسه (جزوه/ویدیو) =====================
    if text in ["ماز", "آلفا اسکول", "تایتان", "کلاسینو"]:
        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return
        state = upload_state[user_id]
        if state.get("mode") == "admin_upload":
            state["institute"] = text
            state["step"] = "subject"
            await message.answer("📚 درس را انتخاب کن", reply_markup=subject_keyboard(state["grade"], state["major"]))
            return
        if state.get("mode") == "user_download":
            state["institute"] = text
            state["step"] = "subject"
            await message.answer("📚 درس را انتخاب کن", reply_markup=subject_keyboard(state["grade"], state["major"]))
            return

    # ===================== درس (جزوه/ویدیو) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "subject":
        state = upload_state[user_id]
        state["subject"] = text
        state["step"] = "teacher"
        if state.get("mode") == "admin_upload":
            kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], text)
            if kb:
                await message.answer("👨‍🏫 دبیر را انتخاب کن", reply_markup=kb)
            else:
                await message.answer("❌ دبیری برای این درس پیدا نشد")
            return
        if state.get("mode") == "user_download":
            state["step"] = "teacher"
            kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], text)
            if kb:
                await message.answer("👨‍🏫 دبیر را انتخاب کن", reply_markup=kb)
            else:
                await message.answer("❌ دبیری برای این درس پیدا نشد")
            return

    # ===================== دبیر (جزوه/ویدیو) =====================
    if user_id in upload_state and upload_state[user_id].get("step") == "teacher":
        state = upload_state[user_id]
        state["teacher"] = text
        if state.get("mode") == "admin_upload":
            state["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            kb.add(KeyboardButton("⚡ ادامه"))
            await message.answer(f"✅ دبیر {text} انتخاب شد.\n\n📤 حالا فایل رو ارسال کن (PDF یا ویدیو)", reply_markup=kb)
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
            await message.answer("📤 فایل بعدی رو بفرست", reply_markup=kb)
            return

    # ===================== لغو =====================
    if text == "❌ لغو":
        if user_id in upload_state:
            del upload_state[user_id]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            KeyboardButton("📚 جزوه"),
            KeyboardButton("🎥 ویدئو"),
            KeyboardButton("📖 کتاب کمک آموزشی"),
            KeyboardButton("📩 ارتباط با ادمین")
        )
        if str(user_id) == str(ADMIN_ID):
            kb.add(KeyboardButton("👑 پنل ادمین"))
        await message.answer("❌ آپلود لغو شد", reply_markup=kb)
        return

    # ===================== دانلود جزوه/ویدیو =====================
    if text in ["📚 جزوه", "🎥 ویدئو"]:
        if user_id in upload_state:
            del upload_state[user_id]
        category_map = {"📚 جزوه": "pdf", "🎥 ویدئو": "video"}
        upload_state[user_id] = {"mode": "user_download", "step": "grade", "category": category_map.get(text, "pdf")}
        await message.answer("کدوم پایه؟", reply_markup=grade_keyboard())
        return

    # ===================== حذف فایل =====================
    if user_id in upload_state:
        state = upload_state[user_id]
        if state.get("mode") == "admin_delete":
            await delete_file(message, text)
            return

    # ===================== لیست فایل‌ها =====================
    if text == "📋 لیست فایل‌ها":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await list_files(message)
        return

    # ===================== حذف فایل (شروع) =====================
    if text == "🗑 حذف فایل":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_delete", "step": "waiting_for_file_id"}
        await message.answer("🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:\n\nمثلاً: `file_123456789`", parse_mode="Markdown")
        return

    # ===================== آمار =====================
    if text == "📊 آمار":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await show_stats(message)
        return

# ===================== نمایش کتاب‌ها =====================
async def show_book_archives(message: types.Message, state: dict):
    user_id = message.from_user.id
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
        await message.answer(f"❌ هیچ کتابی برای این انتخاب‌ها پیدا نشد\n\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            KeyboardButton("📚 جزوه"),
            KeyboardButton("🎥 ویدئو"),
            KeyboardButton("📖 کتاب کمک آموزشی"),
            KeyboardButton("📩 ارتباط با ادمین")
        )
        if str(user_id) == str(ADMIN_ID):
            kb.add(KeyboardButton("👑 پنل ادمین"))
        await message.answer("به منوی اصلی برگشتی", reply_markup=kb)
        if user_id in upload_state:
            del upload_state[user_id]
        return
    for archive in archives:
        caption = f"📖 {archive.file_name}\n📌 {archive.book_name or 'معمولی'}"
        await message.answer_document(archive.file_id, caption=caption)
    if user_id in upload_state:
        del upload_state[user_id]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📚 جزوه"),
        KeyboardButton("🎥 ویدئو"),
        KeyboardButton("📖 کتاب کمک آموزشی"),
        KeyboardButton("📩 ارتباط با ادمین")
    )
    if str(user_id) == str(ADMIN_ID):
        kb.add(KeyboardButton("👑 پنل ادمین"))
    await message.answer("✅ همه کتاب‌ها ارسال شد", reply_markup=kb)

async def list_files(message: types.Message):
    async for db in get_db():
        result = await db.execute(select(Archive).order_by(Archive.id.desc()).limit(20))
        files = result.scalars().all()
    if not files:
        await message.answer("❌ هیچ فایلی در دیتابیس وجود ندارد")
        return
    for file in files:
        category_text = {"pdf": "📄 جزوه", "video": "🎥 ویدیو", "book": "📖 کتاب"}.get(file.category, "📄")
        await message.answer(
            f"{category_text} **{file.file_name}**\n\n"
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
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("⚡ آپلود سریع"),
        KeyboardButton("📤 آپلود جزوه"),
        KeyboardButton("🎥 آپلود ویدئو"),
        KeyboardButton("📖 آپلود کتاب"),
        KeyboardButton("➕ اضافه کردن دبیر"),
        KeyboardButton("➕ اضافه کردن انتشارات"),
        KeyboardButton("📋 لیست فایل‌ها"),
        KeyboardButton("🗑 حذف فایل"),
        KeyboardButton("📊 آمار")
    )
    await message.answer("👑 پنل مدیریت", reply_markup=kb)

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
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("⚡ آپلود سریع"),
        KeyboardButton("📤 آپلود جزوه"),
        KeyboardButton("🎥 آپلود ویدئو"),
        KeyboardButton("📖 آپلود کتاب"),
        KeyboardButton("➕ اضافه کردن دبیر"),
        KeyboardButton("➕ اضافه کردن انتشارات"),
        KeyboardButton("📋 لیست فایل‌ها"),
        KeyboardButton("🗑 حذف فایل"),
        KeyboardButton("📊 آمار")
    )
    await message.answer("👑 پنل مدیریت", reply_markup=kb)

async def show_archives(message: types.Message, state: dict):
    user_id = message.from_user.id
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
        await message.answer(f"❌ هیچ فایلی پیدا نشد\n\n📚 درس: {state['subject']}")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            KeyboardButton("📚 جزوه"),
            KeyboardButton("🎥 ویدئو"),
            KeyboardButton("📖 کتاب کمک آموزشی"),
            KeyboardButton("📩 ارتباط با ادمین")
        )
        if str(user_id) == str(ADMIN_ID):
            kb.add(KeyboardButton("👑 پنل ادمین"))
        await message.answer("به منوی اصلی برگشتی", reply_markup=kb)
        if user_id in upload_state:
            del upload_state[user_id]
        return
    for archive in archives:
        caption = f"📄 {archive.file_name}\n"
        if archive.teacher:
            caption += f"👨‍🏫 دبیر: {archive.teacher}\n"
        if archive.book_name:
            caption += f"📌 {archive.book_name}"
        if archive.category in ["pdf", "book"]:
            await message.answer_document(archive.file_id, caption=caption)
        else:
            await message.answer_video(archive.file_id, caption=caption)
    if user_id in upload_state:
        del upload_state[user_id]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📚 جزوه"),
        KeyboardButton("🎥 ویدئو"),
        KeyboardButton("📖 کتاب کمک آموزشی"),
        KeyboardButton("📩 ارتباط با ادمین")
    )
    if str(user_id) == str(ADMIN_ID):
        kb.add(KeyboardButton("👑 پنل ادمین"))
    await message.answer("✅ همه فایل‌ها ارسال شد", reply_markup=kb)

async def handle_file(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in upload_state:
        await message.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
        return
    
    state = upload_state[user_id]

    # ===================== آپلود سریع =====================
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
        await message.answer(f"✅ فایل با موفقیت ثبت شد!\n📚 {institute} - {grade} - {major} - {subject}", reply_markup=kb)
        return

    # ===================== آپلود کتاب (ادمین) =====================
    if state.get("mode") == "book_upload" and state.get("step") == "waiting_for_file":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        if not message.document:
            await message.answer("❌ لطفاً فایل PDF کتاب رو ارسال کن")
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
                file_id=message.document.file_id,
                file_name=message.document.file_name or "unknown.pdf",
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"))
        kb.add(KeyboardButton("❌ لغو"))
        await message.answer(f"✅ کتاب با موفقیت ثبت شد!\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}", reply_markup=kb)
        return

    # ===================== آپلود جزوه/ویدیو (ادمین) =====================
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
    elif message.video:
        file_id = message.video.file_id
        file_name = f"video_{message.video.file_id[:8]}.mp4"
        file_type = "video"
    else:
        await message.answer("❌ لطفاً فقط فایل PDF یا ویدیو ارسال کن")
        return
    async for db in get_db():
        archive = Archive(
            category=state.get("category", "pdf"),
            type=file_type,
            grade=state["grade"],
            major=state["major"],
            institute=state["institute"],
            subject=state["subject"],
            teacher=state["teacher"],
            file_id=file_id,
            file_name=file_name,
            uploaded_by=user_id
        )
        db.add(archive)
        await db.commit()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("⚡ ادامه"))
    kb.add(KeyboardButton("❌ لغو"))
    await message.answer(f"✅ فایل {file_name} با موفقیت ثبت شد!\n\nبرای آپلود فایل بعدی، روی '⚡ ادامه' بزن", reply_markup=kb)
