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

# ─────────────────────────────────────────────
# کیبورد پنل ادمین (helper تا تکرار نشه)
# ─────────────────────────────────────────────
def admin_keyboard():
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
    return kb

def main_keyboard(user_id):
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

# ─────────────────────────────────────────────
async def cmd_start(message: types.Message):
    user = message.from_user
    async for db in get_db():
        result = await db.execute(select(User).where(User.telegram_id == user.id))
        if not result.scalar_one_or_none():
            db.add(User(telegram_id=user.id, username=user.username, full_name=user.full_name))
            await db.commit()
    await message.answer(
        "🎓 **به بزرگترین آرشیو آموزشی خوش آمدید!**\n\n"
        "📚 **تمامی کلاس‌های سالیانه ۱۴۰۶ پس از شروع در این ربات قرار خواهد گرفت.**\n"
        "✅ **تمامی کلاس‌های نهایی ۱۴۰۵ موسسات ماز | آلفا | تایتان | کلاسینو قرار گرفت.**\n\n"
        "🔹 برای مشاهده جزوه‌ها، دکمه **📚 جزوه** رو بزن\n"
        "🔹 برای مشاهده ویدیوها، دکمه **🎥 ویدئو** رو بزن\n"
        "🔹 برای مشاهده کتاب‌های کمک آموزشی، دکمه **📖 کتاب کمک آموزشی** رو بزن",
        reply_markup=main_keyboard(user.id),
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
async def handle_buttons(message: types.Message):
    text = message.text
    user_id = message.from_user.id

    # ════════════════════════════════════════════
    # ۱. پنل ادمین
    # ════════════════════════════════════════════
    if text == "👑 پنل ادمین":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await message.answer("👑 **پنل مدیریت**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return

    # ════════════════════════════════════════════
    # ۲. ارتباط با ادمین
    # ════════════════════════════════════════════
    if text == "📩 ارتباط با ادمین":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📩 ارسال پیام به ادمین", url="https://t.me/unbrokensociety2026"))
        await message.answer(
            "📩 **ارتباط با ادمین**\n\nبرای ارتباط مستقیم، روی دکمه زیر کلیک کن.",
            reply_markup=kb, parse_mode="Markdown"
        )
        return

    # ════════════════════════════════════════════
    # ۳. آپلود سریع
    # ════════════════════════════════════════════
    if text == "⚡ آپلود سریع":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "fast_upload", "step": "waiting_for_file"}
        await message.answer(
            "⚡ **حالت آپلود سریع فعال شد!**\n\n"
            "📤 فایل رو بفرست و توی کپشن این اطلاعات رو بنویس:\n\n"
            "`نوع | موسسه/ناشر | پایه | رشته | درس | دبیر`\n\n"
            "مثال:\n`جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`\n\n"
            "⚠️ بین اطلاعات فقط `|` بذار",
            parse_mode="Markdown"
        )
        return

    # ════════════════════════════════════════════
    # ۴. آپلود کتاب (ادمین)
    # ════════════════════════════════════════════
    if text == "📖 آپلود کتاب":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "book_upload", "category": "book", "type": "pdf", "step": "publisher"}
        # publisher_keyboard حالا async است
        await message.answer("📖 **آپلود کتاب کمک آموزشی**\n\nناشر رو انتخاب کن:", reply_markup=await publisher_keyboard())
        return

    # ════════════════════════════════════════════
    # ۵. آپلود جزوه
    # ════════════════════════════════════════════
    if text == "📤 آپلود جزوه":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "pdf", "type": "pdf", "step": "grade"}
        await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
        return

    # ════════════════════════════════════════════
    # ۶. آپلود ویدئو
    # ════════════════════════════════════════════
    if text == "🎥 آپلود ویدئو":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_upload", "category": "video", "type": "video", "step": "grade"}
        await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
        return

    # ════════════════════════════════════════════
    # ۷. شروع اضافه کردن انتشارات
    # ════════════════════════════════════════════
    if text == "➕ اضافه کردن انتشارات":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "add_publisher", "step": "ask_name"}
        await message.answer("📝 **اضافه کردن انتشارات جدید**\n\nنام انتشارات رو وارد کن:\n(مثال: ماجرای ۲۰)")
        return

    # ════════════════════════════════════════════
    # ۸. Flow اضافه کردن انتشارات  ← قبل از GRADE
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("mode") == "add_publisher":
        state = upload_state[user_id]

        if state.get("step") == "ask_name":
            state["name"] = text
            state["step"] = "ask_type"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("موسسه آموزشی")
            kb.add("ناشر کتاب")
            await message.answer(f"نوع انتشارات رو انتخاب کن:\n\n📌 {text}", reply_markup=kb)
            return

        if state.get("step") == "ask_type":
            type_map = {"موسسه آموزشی": "institute", "ناشر کتاب": "book_publisher"}
            state["pub_type"] = type_map.get(text, "institute")
            state["step"] = "ask_major_for_subjects"
            state["subjects_data"] = {}
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی")
            kb.add("تجربی")
            kb.add("✅ ثبت نهایی")
            kb.add("❌ لغو")
            await message.answer(
                f"📌 **{state['name']}**\n\n"
                "📚 برای هر رشته، دروس مربوطه رو وارد کن.\n\n"
                "1️⃣ اول رشته رو انتخاب کن (ریاضی یا تجربی)\n"
                "2️⃣ سپس دروس اون رشته رو یکی‌یکی وارد کن\n"
                "3️⃣ وقتی تموم شد، روی **✅ ثبت نهایی** بزن\n\n"
                "⚠️ انسانی فعلاً پشتیبانی نمیشه.",
                reply_markup=kb
            )
            return

        if state.get("step") == "ask_major_for_subjects":
            if text == "✅ ثبت نهایی":
                subjects_data = state.get("subjects_data", {})
                if not subjects_data:
                    await message.answer("❌ حداقل برای یک رشته درس وارد کن!")
                    return
                async for db in get_db():
                    result = await db.execute(select(Publisher).where(Publisher.name == state["name"]))
                    if result.scalar_one_or_none():
                        await message.answer(f"❌ انتشارات {state['name']} قبلاً وجود داره!")
                        del upload_state[user_id]
                        return
                    publisher = Publisher(
                        name=state["name"],
                        type=state["pub_type"],
                        subjects_by_major=subjects_data
                    )
                    db.add(publisher)
                    await db.commit()
                await message.answer(
                    f"✅ انتشارات **{state['name']}** با موفقیت اضافه شد!\n\n"
                    f"📚 دروس ثبت شده:\n" +
                    "\n".join([f"   • {major}: {', '.join(subs)}" for major, subs in subjects_data.items()]),
                    parse_mode="Markdown"
                )
                del upload_state[user_id]
                await message.answer("👑 پنل مدیریت", reply_markup=admin_keyboard())
                return

            elif text == "❌ لغو":
                del upload_state[user_id]
                await message.answer("❌ عملیات لغو شد", reply_markup=admin_keyboard())
                return

            elif text in ["ریاضی", "تجربی"]:
                state["current_major"] = text
                state["step"] = "ask_subject_for_major"
                state["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton(f"✅ ثبت دروس {text}"))
                kb.add(KeyboardButton("🔙 برگشت"))
                await message.answer(
                    f"📌 **{state['name']} - {text}**\n\n"
                    f"دروس رشته {text} رو یکی یکی بنویس.\n"
                    f"وقتی تموم شد روی **✅ ثبت دروس {text}** بزن.",
                    reply_markup=kb
                )
                return

            else:
                await message.answer("❌ لطفاً یکی از گزینه‌های منو رو انتخاب کن.")
                return

        if state.get("step") == "ask_subject_for_major":
            current_major = state.get("current_major", "")
            if text == f"✅ ثبت دروس {current_major}":
                subjects_list = state.get("temp_subjects", [])
                if not subjects_list:
                    await message.answer(f"❌ حداقل یک درس برای {current_major} وارد کن!")
                    return
                state["subjects_data"][current_major] = subjects_list
                state["temp_subjects"] = []
                state["step"] = "ask_major_for_subjects"
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("ریاضی")
                kb.add("تجربی")
                kb.add("✅ ثبت نهایی")
                kb.add("❌ لغو")
                await message.answer(
                    f"✅ دروس {current_major} ثبت شد.\n\n"
                    f"📚 لیست فعلی:\n" +
                    "\n".join([f"   • {m}: {', '.join(s)}" for m, s in state["subjects_data"].items()]) +
                    "\n\nرشته دیگه رو انتخاب کن یا روی **✅ ثبت نهایی** بزن.",
                    reply_markup=kb
                )
                return
            elif text == "🔙 برگشت":
                state["step"] = "ask_major_for_subjects"
                state["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("ریاضی")
                kb.add("تجربی")
                kb.add("✅ ثبت نهایی")
                kb.add("❌ لغو")
                await message.answer("🔙 برگشتی به منوی اصلی.", reply_markup=kb)
                return
            else:
                if text not in state.get("temp_subjects", []):
                    state.setdefault("temp_subjects", []).append(text)
                    await message.answer(
                        f"✅ درس **{text}** به لیست {current_major} اضافه شد.\n\n"
                        f"📚 لیست فعلی:\n" + "\n".join([f"   • {s}" for s in state["temp_subjects"]]),
                        parse_mode="Markdown"
                    )
                else:
                    await message.answer(f"⚠️ درس {text} قبلاً اضافه شده!")
                return

    # ════════════════════════════════════════════
    # ۹. شروع اضافه کردن دبیر
    # ════════════════════════════════════════════
    if text == "➕ اضافه کردن دبیر":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "add_teacher", "step": "ask_name"}
        await message.answer(
            "📝 **اضافه کردن دبیر جدید**\n\n"
            "نام کامل دبیر رو وارد کن:\n(مثال: محمدرضا شجاعی)"
        )
        return

    # ════════════════════════════════════════════
    # ۱۰. Flow اضافه کردن دبیر  ← قبل از GRADE
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("mode") == "add_teacher":
        state = upload_state[user_id]

        if state.get("step") == "ask_name":
            state["name"] = text
            state["step"] = "ask_publisher"
            async for db in get_db():
                result = await db.execute(select(Publisher))
                publishers = result.scalars().all()
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for p in publishers:
                kb.add(p.name)
            kb.add("❌ لغو")
            await message.answer(
                f"📌 دبیر: {state['name']}\n\nانتشارات/موسسه مربوطه رو انتخاب کن:",
                reply_markup=kb
            )
            return

        if state.get("step") == "ask_publisher":
            if text == "❌ لغو":
                del upload_state[user_id]
                await message.answer("❌ عملیات لغو شد", reply_markup=admin_keyboard())
                return
            async for db in get_db():
                result = await db.execute(select(Publisher).where(Publisher.name == text))
                publisher = result.scalar_one_or_none()
                if not publisher:
                    await message.answer("❌ انتشارات پیدا نشد. دوباره انتخاب کن.")
                    return
                state["publisher_id"] = publisher.id
                state["publisher_name"] = publisher.name
            state["step"] = "ask_grade"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("دهم", "یازدهم", "دوازدهم")
            await message.answer(
                f"📌 دبیر: {state['name']}\n"
                f"🏛 انتشارات: {state['publisher_name']}\n\n"
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
                f"🏛 انتشارات: {state['publisher_name']}\n"
                f"📚 پایه: {text}\n\n"
                "رشته رو انتخاب کن:",
                reply_markup=kb
            )
            return

        if state.get("step") == "ask_major":
            state["major"] = text
            state["step"] = "ask_subject"
            subject_list = {
                "ریاضی": ["فیزیک","شیمی","ریاضی","هندسه","فارسی","عربی","حسابان","گسسته","آمار و احتمال"],
                "تجربی": ["زیست شناسی","شیمی","فیزیک","ریاضی","فارسی","عربی"],
                "انسانی": ["علوم و فنون ادبی","ریاضی و آمار","جامعه شناسی","منطق","اقتصاد","فارسی",
                           "روان شناسی","فلسفه","عربی تخصصی","دین و زندگی","فلسفه و منطق","تاریخ","جغرافیا","دینی"]
            }
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subject_list.get(text, []):
                kb.add(s)
            kb.add("❌ لغو")
            await message.answer(
                f"📌 دبیر: {state['name']}\n"
                f"🏛 انتشارات: {state['publisher_name']}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {text}\n\n"
                "درس رو انتخاب کن:",
                reply_markup=kb
            )
            return

        if state.get("step") == "ask_subject":
            if text == "❌ لغو":
                del upload_state[user_id]
                await message.answer("❌ عملیات لغو شد", reply_markup=admin_keyboard())
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
                f"✅ دبیر **{state['name']}** با موفقیت اضافه شد!\n\n"
                f"📚 {state['grade']} - {state['major']} - {state['subject']}\n"
                f"🏛 {state['publisher_name']}",
                parse_mode="Markdown"
            )
            del upload_state[user_id]
            await message.answer("👑 پنل مدیریت", reply_markup=admin_keyboard())
            return

    # ════════════════════════════════════════════
    # ۱۱. دانلود کتاب (کاربر)
    # ════════════════════════════════════════════
    if text == "📖 کتاب کمک آموزشی":
        if user_id in upload_state:
            del upload_state[user_id]
        upload_state[user_id] = {"mode": "user_download", "step": "book_grade", "category": "book"}
        await message.answer("📖 کدوم پایه؟", reply_markup=grade_keyboard())
        return

    # ════════════════════════════════════════════
    # ۱۲. GRADE handler
    # ════════════════════════════════════════════
    if text in ["دهم", "یازدهم", "دوازدهم"]:
        if user_id not in upload_state:
            upload_state[user_id] = {"mode": "user_download", "step": "major", "grade": text}
            await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
            return

        state = upload_state[user_id]

        if state.get("step") == "book_grade":
            state["grade"] = text
            state["step"] = "book_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{text}|ریاضی"))
            kb.add(KeyboardButton(f"رشته:{text}|تجربی"))
            await message.answer("📖 رشته را انتخاب کن:", reply_markup=kb)
            return

        if state.get("mode") == "book_upload":
            state["grade"] = text
            state["step"] = "major"
            await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
            return

        if state.get("mode") == "admin_upload":
            state["grade"] = text
            state["step"] = "major"
            await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
            return

        # user_download عادی
        if user_id in upload_state:
            del upload_state[user_id]
        upload_state[user_id] = {"mode": "user_download", "step": "major", "grade": text}
        await message.answer("رشته را انتخاب کن", reply_markup=major_keyboard(text))
        return

    # ════════════════════════════════════════════
    # ۱۳. ناشران (آپلود کتاب ادمین) - از دیتابیس میاد پس هر اسمی ممکنه
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("mode") == "book_upload" and upload_state[user_id].get("step") == "publisher":
        state = upload_state[user_id]
        # بررسی که ناشر در دیتابیس وجود داره
        async for db in get_db():
            result = await db.execute(select(Publisher).where(Publisher.name == text))
            publisher = result.scalar_one_or_none()
        if publisher:
            state["publisher"] = text
            state["step"] = "grade"
            await message.answer("پایه را انتخاب کن", reply_markup=grade_keyboard())
            return

    # ════════════════════════════════════════════
    # ۱۴. MAJOR handler
    # ════════════════════════════════════════════
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
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=institute_keyboard())
            return

        if state.get("mode") == "user_download":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"
            await message.answer("🏛 موسسه را انتخاب کن", reply_markup=institute_keyboard())
            return

    # ════════════════════════════════════════════
    # ۱۵. کتاب: انتخاب ناشر (دانلود کاربر) - از دیتابیس
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("step") == "book_publisher":
        state = upload_state[user_id]
        # هر ناشری که از دیتابیس اومده رو قبول میکنیم
        async for db in get_db():
            result = await db.execute(select(Publisher).where(Publisher.name == text))
            publisher = result.scalar_one_or_none()
        if publisher:
            state["publisher"] = text
            state["step"] = "book_subject_download"
            await message.answer(
                "📖 درس مورد نظر رو انتخاب کن:",
                reply_markup=await book_subject_keyboard(text, state["grade"], state["major"])
            )
            return

    # ════════════════════════════════════════════
    # ۱۶. کتاب: انتخاب درس (دانلود)
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("step") == "book_subject_download":
        state = upload_state[user_id]
        state["subject"] = text
        await show_book_archives(message, state)
        return

    # ════════════════════════════════════════════
    # ۱۷. کتاب: انتخاب درس (آپلود ادمین)
    # ════════════════════════════════════════════
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

    # ════════════════════════════════════════════
    # ۱۸. موسسه (جزوه/ویدیو)
    # ════════════════════════════════════════════
    if text in ["ماز", "آلفا اسکول", "تایتان", "کلاسینو"]:
        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return
        state = upload_state[user_id]
        if state.get("mode") in ["admin_upload", "user_download"]:
            state["institute"] = text
            state["step"] = "subject"
            await message.answer("📚 درس را انتخاب کن", reply_markup=subject_keyboard(state["grade"], state["major"]))
            return

    # ════════════════════════════════════════════
    # ۱۹. درس (جزوه/ویدیو)
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("step") == "subject":
        state = upload_state[user_id]
        state["subject"] = text
        state["step"] = "teacher"
        kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], text)
        if kb:
            await message.answer("👨‍🏫 دبیر را انتخاب کن", reply_markup=kb)
        else:
            await message.answer("❌ دبیری برای این درس پیدا نشد")
        return

    # ════════════════════════════════════════════
    # ۲۰. دبیر (جزوه/ویدیو)
    # ════════════════════════════════════════════
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

    # ════════════════════════════════════════════
    # ۲۱. ادامه آپلود
    # ════════════════════════════════════════════
    if text == "⚡ ادامه":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        if user_id in upload_state:
            upload_state[user_id]["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            await message.answer("📤 فایل بعدی رو بفرست", reply_markup=kb)
            return

    # ════════════════════════════════════════════
    # ۲۲. لغو
    # ════════════════════════════════════════════
    if text == "❌ لغو":
        if user_id in upload_state:
            del upload_state[user_id]
        await message.answer("❌ لغو شد", reply_markup=main_keyboard(user_id))
        return

    # ════════════════════════════════════════════
    # ۲۳. دانلود جزوه/ویدیو
    # ════════════════════════════════════════════
    if text in ["📚 جزوه", "🎥 ویدئو"]:
        if user_id in upload_state:
            del upload_state[user_id]
        category_map = {"📚 جزوه": "pdf", "🎥 ویدئو": "video"}
        upload_state[user_id] = {"mode": "user_download", "step": "grade", "category": category_map[text]}
        await message.answer("کدوم پایه؟", reply_markup=grade_keyboard())
        return

    # ════════════════════════════════════════════
    # ۲۴. حذف فایل (ادمین)
    # ════════════════════════════════════════════
    if user_id in upload_state and upload_state[user_id].get("mode") == "admin_delete":
        await delete_file(message, text)
        return

    if text == "📋 لیست فایل‌ها":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await list_files(message)
        return

    if text == "🗑 حذف فایل":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        upload_state[user_id] = {"mode": "admin_delete", "step": "waiting_for_file_id"}
        await message.answer("🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:", parse_mode="Markdown")
        return

    if text == "📊 آمار":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        await show_stats(message)
        return


# ─────────────────────────────────────────────
# توابع کمکی
# ─────────────────────────────────────────────
async def show_book_archives(message: types.Message, state: dict):
    user_id = message.from_user.id
    async for db in get_db():
        result = await db.execute(
            select(Archive).where(
                Archive.category == "book",
                Archive.grade == state["grade"],
                Archive.major == state["major"],
                Archive.institute == state["publisher"],
                Archive.subject == state["subject"]
            )
        )
        archives = result.scalars().all()
    if not archives:
        await message.answer(
            f"❌ هیچ کتابی برای این انتخاب‌ها پیدا نشد\n\n"
            f"📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}"
        )
        if user_id in upload_state:
            del upload_state[user_id]
        await message.answer("به منوی اصلی برگشتی", reply_markup=main_keyboard(user_id))
        return
    for archive in archives:
        caption = f"📖 {archive.file_name}\n📌 {archive.book_name or 'معمولی'}"
        await message.answer_document(archive.file_id, caption=caption)
    if user_id in upload_state:
        del upload_state[user_id]
    await message.answer("✅ همه کتاب‌ها ارسال شد", reply_markup=main_keyboard(user_id))


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
        if user_id in upload_state:
            del upload_state[user_id]
        await message.answer("به منوی اصلی برگشتی", reply_markup=main_keyboard(user_id))
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
    await message.answer("✅ همه فایل‌ها ارسال شد", reply_markup=main_keyboard(user_id))


async def list_files(message: types.Message):
    async for db in get_db():
        result = await db.execute(select(Archive).order_by(Archive.id.desc()).limit(20))
        files = result.scalars().all()
    if not files:
        await message.answer("❌ هیچ فایلی در دیتابیس وجود ندارد")
        return
    for file in files:
        cat = {"pdf": "📄 جزوه", "video": "🎥 ویدیو", "book": "📖 کتاب"}.get(file.category, "📄")
        await message.answer(
            f"{cat} **{file.file_name}**\n\n"
            f"📚 پایه: {file.grade} | 🎓 رشته: {file.major}\n"
            f"🏛 موسسه/ناشر: {file.institute}\n"
            f"📖 درس: {file.subject} | 👨‍🏫 دبیر: {file.teacher or 'ندارد'}",
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
    await message.answer("👑 پنل مدیریت", reply_markup=admin_keyboard())


async def show_stats(message: types.Message):
    async for db in get_db():
        users_count  = await db.scalar(select(func.count()).select_from(User))
        files_count  = await db.scalar(select(func.count()).select_from(Archive))
        pdf_count    = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "pdf"))
        video_count  = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "video"))
        book_count   = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "book"))
    await message.answer(
        f"📊 **آمار ربات**\n\n"
        f"👥 کاربران: {users_count}\n"
        f"📄 کل فایل‌ها: {files_count}\n"
        f"📁 جزوه: {pdf_count}\n"
        f"🎥 ویدیو: {video_count}\n"
        f"📖 کتاب: {book_count}",
        parse_mode="Markdown"
    )
    await message.answer("👑 پنل مدیریت", reply_markup=admin_keyboard())


async def handle_file(message: types.Message):
    user_id = message.from_user.id
    if user_id not in upload_state:
        await message.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
        return
    state = upload_state[user_id]

    # ════ آپلود سریع ════
    if state.get("mode") == "fast_upload":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        caption = message.caption or ""
        parts = [p.strip() for p in caption.split("|")]
        if len(parts) < 5:
            await message.answer("❌ فرمت کپشن اشتباهه!\n\nمثال: `جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`", parse_mode="Markdown")
            return
        category_map = {"جزوه": "pdf", "ویدیو": "video", "کتاب": "book"}
        async for db in get_db():
            archive = Archive(
                category=category_map.get(parts[0], "pdf"),
                type="pdf" if message.document else "video",
                grade=parts[2], major=parts[3], institute=parts[1], subject=parts[4],
                teacher=parts[5] if len(parts) > 5 else None,
                book_name=parts[6] if len(parts) > 6 else None,
                file_id=message.document.file_id if message.document else message.video.file_id,
                file_name=message.document.file_name if message.document else f"video_{message.message_id}.mp4",
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"), KeyboardButton("❌ لغو"))
        await message.answer(f"✅ فایل با موفقیت ثبت شد!\n📚 {parts[1]} - {parts[2]} - {parts[3]} - {parts[4]}", reply_markup=kb)
        return

    # ════ آپلود کتاب ════
    if state.get("mode") == "book_upload" and state.get("step") == "waiting_for_file":
        if str(user_id) != str(ADMIN_ID):
            await message.answer("⛔ دسترسی نداری")
            return
        if not message.document:
            await message.answer("❌ لطفاً فایل PDF کتاب رو ارسال کن")
            return
        async for db in get_db():
            archive = Archive(
                category="book", type="pdf",
                grade=state["grade"], major=state["major"], institute=state["publisher"],
                subject=state["subject"], teacher=None,
                book_name=state.get("book_name", "معمولی"),
                file_id=message.document.file_id,
                file_name=message.document.file_name or "unknown.pdf",
                uploaded_by=user_id
            )
            db.add(archive)
            await db.commit()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⚡ ادامه"), KeyboardButton("❌ لغو"))
        await message.answer(
            f"✅ کتاب با موفقیت ثبت شد!\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}",
            reply_markup=kb
        )
        return

    # ════ آپلود جزوه/ویدیو ════
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
            category=state.get("category", "pdf"), type=file_type,
            grade=state["grade"], major=state["major"], institute=state["institute"],
            subject=state["subject"], teacher=state["teacher"],
            file_id=file_id, file_name=file_name, uploaded_by=user_id
        )
        db.add(archive)
        await db.commit()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("⚡ ادامه"), KeyboardButton("❌ لغو"))
    await message.answer(f"✅ فایل **{file_name}** با موفقیت ثبت شد!\n\nبرای فایل بعدی روی '⚡ ادامه' بزن", reply_markup=kb, parse_mode="Markdown")
