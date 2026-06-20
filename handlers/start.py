from aiogram import types
from sqlalchemy import select, func

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
        kb.add("📋 لیست فایل‌ها")
        kb.add("🗑 حذف فایل")
        kb.add("📊 آمار")

        await message.answer(
            "👑 پنل مدیریت",
            reply_markup=kb
        )
        return


    # =====================
    # LIST FILES (لیست فایل‌ها)
    # =====================
    elif text == "📋 لیست فایل‌ها":

        await list_files(message)
        return


    # =====================
    # DELETE FILE (حذف فایل)
    # =====================
    elif text == "🗑 حذف فایل":

        # ذخیره وضعیت حذف
        upload_state[user_id] = {
            "mode": "admin_delete",
            "step": "waiting_for_file_id"
        }

        await message.answer(
            "🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:\n\n"
            "مثلاً: `file_123456789`",
            parse_mode="Markdown"
        )
        return


    # =====================
    # STATS (آمار)
    # =====================
    elif text == "📊 آمار":

        await show_stats(message)
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
                "step": "major",
                "grade": text
            }

            await message.answer(
                "رشته را انتخاب کن",
                reply_markup=major_keyboard(text)
            )
            return


    # =====================
    # DELETE FILE - دریافت آیدی فایل
    # =====================
    elif user_id in upload_state and upload_state[user_id].get("mode") == "admin_delete":
        
        if upload_state[user_id].get("step") == "waiting_for_file_id":
            file_id = text.strip()
            await delete_file(message, file_id)
            return


    # =====================
    # MAJOR (هم برای آپلود و هم دانلود)
    # =====================
    elif text.startswith("رشته:"):

        if user_id not in upload_state:
            await message.answer("❌ لطفاً از ابتدا شروع کن")
            return

        grade, major = text.replace("رشته:", "").split("|")

        state = upload_state[user_id]

        # اگر کاربر برای آپلود هست
        if state.get("mode") == "admin_upload":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"

            await message.answer(
                "🏛 موسسه را انتخاب کن",
                reply_markup=institute_keyboard()
            )
            return

        # اگر کاربر برای دانلود هست
        elif state.get("mode") == "user_download":
            state["grade"] = grade
            state["major"] = major
            state["step"] = "institute"

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

        # برای هر دو حالت (آپلود و دانلود) دبیر رو نمایش بده
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
    # TEACHER SELECTED (هم برای آپلود و هم دانلود)
    # =====================
    elif user_id in upload_state and upload_state[user_id].get("step") == "teacher":

        state = upload_state[user_id]
        teacher = text
        state["teacher"] = teacher
        state["step"] = "waiting_for_file"

        # اگر کاربر برای آپلود هست
        if state.get("mode") == "admin_upload":
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("❌ لغو")

            await message.answer(
                f"✅ دبیر {teacher} انتخاب شد.\n\n"
                f"📤 حالا فایل رو ارسال کن (PDF یا ویدیو)",
                reply_markup=kb
            )
            return

        # اگر کاربر برای دانلود هست
        elif state.get("mode") == "user_download":
            # نمایش فایل‌های اون دبیر خاص
            await show_archives(message, state)
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
# LIST FILES (لیست فایل‌ها)
# =========================
async def list_files(message: types.Message):

    user_id = message.from_user.id

    async for db in get_db():

        result = await db.execute(
            select(Archive).order_by(Archive.id.desc()).limit(20)
        )
        files = result.scalars().all()

    if not files:
        await message.answer("❌ هیچ فایلی در دیتابیس وجود ندارد")
        return

    # ارسال لیست فایل‌ها به صورت تکی
    for file in files:
        await message.answer(
            f"📄 **{file.file_name}**\n\n"
            f"🆔 آیدی فایل: `{file.file_id[:20]}...`\n"
            f"📚 پایه: {file.grade}\n"
            f"🎓 رشته: {file.major}\n"
            f"🏛 موسسه: {file.institute}\n"
            f"📖 درس: {file.subject}\n"
            f"👨‍🏫 دبیر: {file.teacher}\n"
            f"📁 نوع: {'PDF' if file.type == 'pdf' else 'ویدیو'}\n"
            f"👤 آپلود کننده: {file.uploaded_by}",
            parse_mode="Markdown"
        )

    await message.answer(
        f"✅ {len(files)} فایل آخر نمایش داده شد"
    )


# =========================
# DELETE FILE (حذف فایل)
# =========================
async def delete_file(message: types.Message, file_id: str):

    user_id = message.from_user.id

    # جستجوی فایل با آیدی کامل یا بخشی از آن
    async for db in get_db():

        # اگر آیدی کامل وارد شده
        result = await db.execute(
            select(Archive).where(Archive.file_id == file_id)
        )
        file = result.scalar_one_or_none()

        # اگر با آیدی کامل پیدا نشد، با بخشی از آیدی جستجو کن
        if not file:
            result = await db.execute(
                select(Archive).where(Archive.file_id.like(f"%{file_id}%"))
            )
            file = result.scalar_one_or_none()

        if file:
            # حذف فایل
            await db.delete(file)
            await db.commit()

            await message.answer(
                f"✅ فایل با موفقیت حذف شد:\n\n"
                f"📄 {file.file_name}\n"
                f"👨‍🏫 دبیر: {file.teacher}\n"
                f"📖 درس: {file.subject}"
            )
        else:
            await message.answer(
                f"❌ فایلی با آیدی `{file_id}` پیدا نشد\n\n"
                "لطفاً آیدی صحیح رو وارد کن"
            )

    # پاک کردن حالت
    if user_id in upload_state:
        del upload_state[user_id]

    # برگشت به پنل ادمین
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📤 آپلود جزوه")
    kb.add("🎥 آپلود ویدئو")
    kb.add("📋 لیست فایل‌ها")
    kb.add("🗑 حذف فایل")
    kb.add("📊 آمار")

    await message.answer(
        "👑 پنل مدیریت",
        reply_markup=kb
    )


# =========================
# SHOW STATS (آمار)
# =========================
async def show_stats(message: types.Message):

    user_id = message.from_user.id

    async for db in get_db():

        # تعداد کل کاربران
        users_count = await db.scalar(
            select(func.count()).select_from(User)
        )

        # تعداد کل فایل‌ها
        files_count = await db.scalar(
            select(func.count()).select_from(Archive)
        )

        # تعداد فایل‌های PDF
        pdf_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.type == "pdf")
        )

        # تعداد فایل‌های ویدیو
        video_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.type == "video")
        )

        # تعداد فایل‌های هر موسسه
        maz_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.institute == "ماز")
        )
        alpha_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.institute == "آلفا اسکول")
        )
        titan_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.institute == "تایتان")
        )
        classino_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.institute == "کلاسینو")
        )

        # تعداد فایل‌های هر پایه
        tenth_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.grade == "دهم")
        )
        eleventh_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.grade == "یازدهم")
        )
        twelfth_count = await db.scalar(
            select(func.count()).select_from(Archive).where(Archive.grade == "دوازدهم")
        )

    # ارسال آمار
    await message.answer(
        f"📊 **آمار ربات**\n\n"
        f"👥 **کاربران:** {users_count}\n"
        f"📄 **کل فایل‌ها:** {files_count}\n\n"
        f"📁 **نوع فایل:**\n"
        f"   📄 PDF: {pdf_count}\n"
        f"   🎥 ویدیو: {video_count}\n\n"
        f"🏛 **موسسه:**\n"
        f"   ماز: {maz_count}\n"
        f"   آلفا اسکول: {alpha_count}\n"
        f"   تایتان: {titan_count}\n"
        f"   کلاسینو: {classino_count}\n\n"
        f"📚 **پایه:**\n"
        f"   دهم: {tenth_count}\n"
        f"   یازدهم: {eleventh_count}\n"
        f"   دوازدهم: {twelfth_count}",
        parse_mode="Markdown"
    )

    # برگشت به پنل ادمین
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📤 آپلود جزوه")
    kb.add("🎥 آپلود ویدئو")
    kb.add("📋 لیست فایل‌ها")
    kb.add("🗑 حذف فایل")
    kb.add("📊 آمار")

    await message.answer(
        "👑 پنل مدیریت",
        reply_markup=kb
    )


# =========================
# نمایش فایل‌ها (برای کاربر عادی)
# =========================
async def show_archives(message: types.Message, state: dict):

    user_id = message.from_user.id

    # گرفتن فایل‌ها از دیتابیس با فیلتر دبیر
    async for db in get_db():

        result = await db.execute(
            select(Archive).where(
                Archive.grade == state["grade"],
                Archive.major == state["major"],
                Archive.institute == state["institute"],
                Archive.subject == state["subject"],
                Archive.teacher == state["teacher"],
                Archive.type == state.get("type", "pdf")
            )
        )

        archives = result.scalars().all()

    if not archives:
        await message.answer(
            f"❌ هیچ فایلی برای این انتخاب‌ها پیدا نشد\n\n"
            f"📚 درس: {state['subject']}\n"
            f"👨‍🏫 دبیر: {state['teacher']}"
        )
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
