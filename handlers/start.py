from aiogram import types
from sqlalchemy import select

from database.core import get_db
from database.models import User, Archive

from bot.keyboards.archive import (
    grade_keyboard,
    major_keyboard,
    institute_keyboard,
    subject_keyboard,
    teacher_keyboard
)

from handlers.state import upload_state


ADMIN_ID = 7336595194


# =========================
# START
# =========================
async def cmd_start(message: types.Message):

    user = message.from_user

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        "📚 جزوه",
        "🎥 ویدئو"
    )

    if str(user.id) == str(ADMIN_ID):
        kb.add("👑 پنل ادمین")

    await message.answer(
        "🎓 خوش اومدی",
        reply_markup=kb
    )

    async for db in get_db():

        result = await db.execute(
            select(User).where(User.telegram_id == user.id)
        )

        if not result.scalar_one_or_none():

            db.add(
                User(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )
            )

            await db.commit()


# =========================
# HANDLE BUTTONS
# =========================
async def handle_buttons(message: types.Message):

    text = message.text
    user_id = message.from_user.id


    # =====================
    # ADMIN PANEL
    # =====================
    if text == "👑 پنل ادمین":

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add("📤 آپلود جزوه")
        kb.add("🎥 آپلود ویدئو")

        await message.answer(
            "پنل مدیریت",
            reply_markup=kb
        )
        return


    # =====================
    # START UPLOAD (فقط ادمین)
    # =====================
    elif text in ["📤 آپلود جزوه", "🎥 آپلود ویدئو"]:

        upload_state[user_id] = {
            "mode": "admin_upload",
            "type": "pdf" if text == "📤 آپلود جزوه" else "video",
            "step": "grade"
        }

        await message.answer(
            "پایه را انتخاب کن",
            reply_markup=grade_keyboard()
        )
        return


    # =====================
    # GRADE (برای آپلود)
    # =====================
    elif text in ["دهم", "یازدهم", "دوازدهم"]:

        # چک میکنیم کاربر در حالت آپلود هست یا دانلود
        if user_id in upload_state and upload_state[user_id].get("mode") == "admin_upload":
            upload_state[user_id]["grade"] = text
            upload_state[user_id]["step"] = "major"

            await message.answer(
                "رشته را انتخاب کن",
                reply_markup=major_keyboard(text)
            )
            return

        # اگر کاربر عادی باشه و برای دانلود پایه رو انتخاب کنه
        elif text in ["دهم", "یازدهم", "دوازدهم"]:
            # ذخیره وضعیت دانلود
            upload_state[user_id] = {
                "mode": "user_download",
                "step": "institute",
                "grade": text
            }

            await message.answer(
                "🏛 موسسه را انتخاب کن",
                reply_markup=institute_keyboard()
            )
            return


    # =====================
    # MAJOR (برای آپلود)
    # =====================
    elif text.startswith("رشته:"):

        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return

        grade, major = text.replace("رشته:", "").split("|")

        if upload_state[user_id].get("mode") == "admin_upload":
            upload_state[user_id]["grade"] = grade
            upload_state[user_id]["major"] = major
            upload_state[user_id]["step"] = "institute"

            await message.answer(
                "🏛 موسسه را انتخاب کن",
                reply_markup=institute_keyboard()
            )
            return


    # =====================
    # INSTITUTE (هم برای آپلود و هم دانلود)
    # =====================
    elif text in ["ماز", "آلفا اسکول", "تایتان", "کلاسینو"]:

        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return

        state = upload_state[user_id]

        # اگر کاربر برای دانلود انتخاب کرده
        if state.get("mode") == "user_download":
            state["institute"] = text
            state["step"] = "subject"

            await message.answer(
                "📚 درس را انتخاب کن",
                reply_markup=subject_keyboard(
                    state["grade"],
                    "ریاضی"  # موقتی، بعداً اصلاح میشه
                )
            )
            return

        # اگر کاربر برای آپلود انتخاب کرده
        elif state.get("mode") == "admin_upload":
            state["institute"] = text
            state["step"] = "subject"

            await message.answer(
                "📚 درس را انتخاب کن",
                reply_markup=subject_keyboard(
                    state["grade"],
                    state["major"]
                )
            )
            return


    # =====================
    # SUBJECT (هم برای آپلود و هم دانلود)
    # =====================
    elif user_id in upload_state and upload_state[user_id].get("step") == "subject":

        state = upload_state[user_id]
        subject = text
        state["subject"] = subject
        state["step"] = "teacher"

        # اگر کاربر برای دانلود هست، نیازی به انتخاب دبیر نداره
        if state.get("mode") == "user_download":
            # نمایش لیست دبیرها و فایل‌ها
            await show_archives(message, state)
            return

        # اگر کاربر برای آپلود هست
        elif state.get("mode") == "admin_upload":
            kb = teacher_keyboard(
                state["grade"],
                state["major"],
                state["institute"],
                subject
            )

            await message.answer(
                "👨‍🏫 دبیر را انتخاب کن",
                reply_markup=kb
            )
            return


    # =====================
    # TEACHER SELECTED (فقط برای آپلود)
    # =====================
    elif user_id in upload_state and upload_state[user_id].get("step") == "teacher":

        state = upload_state[user_id]
        teacher = text
        state["teacher"] = teacher
        state["step"] = "waiting_for_file"

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("❌ لغو")

        await message.answer(
            f"✅ دبیر {teacher} انتخاب شد.\n\n"
            f"📤 حالا فایل رو ارسال کن (PDF یا ویدیو)",
            reply_markup=kb
        )
        return


    # =====================
    # CANCEL
    # =====================
    elif text == "❌ لغو":

        if user_id in upload_state:
            del upload_state[user_id]

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📚 جزوه", "🎥 ویدئو")

        if str(user_id) == str(ADMIN_ID):
            kb.add("👑 پنل ادمین")

        await message.answer(
            "❌ آپلود لغو شد",
            reply_markup=kb
        )
        return


    # =====================
    # USER MODE (دانلود جزوه یا ویدئو)
    # =====================
    elif text in ["📚 جزوه", "🎥 ویدئو"]:

        # شروع فرآیند دانلود
        upload_state[user_id] = {
            "mode": "user_download",
            "step": "grade",
            "type": "pdf" if text == "📚 جزوه" else "video"
        }

        await message.answer(
            "کدوم پایه؟",
            reply_markup=grade_keyboard()
        )
        return


# =========================
# نمایش فایل‌ها
# =========================
async def show_archives(message: types.Message, state: dict):

    user_id = message.from_user.id

    # گرفتن فایل‌ها از دیتابیس
    async for db in get_db():

        result = await db.execute(
            select(Archive).where(
                Archive.grade == state["grade"],
                Archive.institute == state["institute"],
                Archive.subject == state["subject"],
                Archive.type == state.get("type", "pdf")
            )
        )

        archives = result.scalars().all()

    if not archives:
        await message.answer("❌ هیچ فایلی برای این انتخاب‌ها پیدا نشد")
        # برگشت به منوی اصلی
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📚 جزوه", "🎥 ویدئو")
        if str(user_id) == str(ADMIN_ID):
            kb.add("👑 پنل ادمین")
        await message.answer("به منوی اصلی برگشتی", reply_markup=kb)
        if user_id in upload_state:
            del upload_state[user_id]
        return

    # ارسال فایل‌ها
    for archive in archives:
        if archive.type == "pdf":
            await message.answer_document(
                archive.file_id,
                caption=f"📄 {archive.file_name}\n"
                        f"👨‍🏫 دبیر: {archive.teacher}"
            )
        else:  # video
            await message.answer_video(
                archive.file_id,
                caption=f"🎥 {archive.file_name}\n"
                        f"👨‍🏫 دبیر: {archive.teacher}"
            )

    # پاک کردن وضعیت دانلود
    if user_id in upload_state:
        del upload_state[user_id]

    # برگشت به منوی اصلی
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 جزوه", "🎥 ویدئو")
    if str(user_id) == str(ADMIN_ID):
        kb.add("👑 پنل ادمین")

    await message.answer(
        "✅ همه فایل‌ها ارسال شد",
        reply_markup=kb
    )


# =========================
# HANDLE FILE UPLOAD (فقط ادمین)
# =========================
async def handle_file(message: types.Message):

    user_id = message.from_user.id

    # بررسی اینکه کاربر در حالت آپلود هست یا نه
    if user_id not in upload_state:
        await message.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
        return

    state = upload_state[user_id]

    if state.get("mode") != "admin_upload":
        await message.answer("❌ شما در حالت دانلود هستید")
        return

    if state.get("step") != "waiting_for_file":
        await message.answer("❌ لطفاً اول دبیر رو انتخاب کن")
        return

    # دریافت فایل
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

    # ذخیره در دیتابیس
    async for db in get_db():

        archive = Archive(
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

    # پاک کردن حالت آپلود
    del upload_state[user_id]

    # برگشت به منوی اصلی
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 جزوه", "🎥 ویدئو")

    if str(user_id) == str(ADMIN_ID):
        kb.add("👑 پنل ادمین")

    await message.answer(
        f"✅ فایل {file_name} با موفقیت ثبت شد!",
        reply_markup=kb
    )
