from aiogram import types
from sqlalchemy import select, func
from database.core import get_db
from database.models import User, Archive, Publisher, Teacher
from bot.keyboards.archive import *
from handlers.state import upload_state
from aiogram.types import KeyboardButton
import re, asyncio
from datetime import datetime

ADMIN_ID = 7336595194
CHANNEL_ID = -1002505515904
CHANNEL_LINK = "https://t.me/School_learny"

async def main_menu(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*[KeyboardButton(b) for b in ["📚 جزوه", "🎥 ویدئو", "📖 کتاب کمک آموزشی", "📩 ارتباط با ادمین"]])
    if str(user_id) == str(ADMIN_ID): kb.add(KeyboardButton("👑 پنل ادمین"))
    return kb

async def check_subscription(user_id, bot):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, user_id)
        return m.status in ["member", "administrator", "creator"]
    except: return True

async def send_join_message(m):
    kb = types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK))
    await m.answer("🔒 **برای استفاده از ربات باید عضو کانال ما باشید.**\n\n👇 روی دکمه زیر کلیک کنید، عضو شوید و سپس **/start** رو بزنید.", reply_markup=kb, parse_mode="Markdown")

async def send_file_with_timer(bot, chat_id, file_id, caption="", delay=30, is_video=False):
    if is_video:
        sent = await bot.send_video(chat_id, file_id, caption=caption)
    else:
        sent = await bot.send_document(chat_id, file_id, caption=caption)
    timer = await bot.send_message(chat_id, f"⏳ **این فایل تا {delay} ثانیه دیگه پاک میشه!**\n\n⬇️ لطفاً سریع دانلود کنید.\n\n🕐 {delay} ثانیه مهلت دارید.", parse_mode="Markdown")
    async def delete():
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id, timer.message_id)
            await bot.delete_message(chat_id, sent.message_id)
        except: pass
    asyncio.create_task(delete())
    return sent

def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    [kb.add(*[KeyboardButton(b) for b in row]) for row in [
        ["⚡ آپلود سریع", "📤 آپلود جزوه", "🎥 آپلود ویدئو", "📖 آپلود کتاب"],
        ["🗑 حذف دبیر", "➕ اضافه کردن انتشارات"],
        ["📋 لیست فایل‌ها", "🗑 حذف فایل"],
        ["👥 لیست کاربران", "📊 آمار"],
        ["⚙️ تنظیمات", "💾 بکاپ", "🔙 برگشت به منو"]
    ]]
    return kb

async def cmd_start(m: types.Message):
    if not await check_subscription(m.from_user.id, m.bot): return await send_join_message(m)
    async for db in get_db():
        if not await db.scalar(select(User).where(User.telegram_id == m.from_user.id)):
            db.add(User(telegram_id=m.from_user.id, username=m.from_user.username, full_name=m.from_user.full_name))
            await db.commit()
    await m.answer("🎓 **به بزرگترین آرشیو آموزشی خوش آمدید!**\n\n📚 **سالیانه‌های ۱۴۰۶ در دسترس قرار گرفت!**\n✅ **کلاس‌های آلفا اسکول شروع شد!**\n\n🔹 برای مشاهده جزوه‌ها، دکمه **📚 جزوه** رو بزن\n🔹 برای مشاهده ویدیوها، دکمه **🎥 ویدئو** رو بزن\n🔹 برای مشاهده کتاب‌های کمک آموزشی، دکمه **📖 کتاب کمک آموزشی** رو بزن\n\n💡 **نکته:** برای برگشت از هر مرحله‌ای، روی دکمه **🔙 برگشت به منو** کلیک کن یا دستور **/start** رو بزن.", reply_markup=await main_menu(m.from_user.id), parse_mode="Markdown")

async def auto_save_from_channel(m: types.Message):
    if not (m.chat.id == CHANNEL_ID or (m.forward_from_chat and m.forward_from_chat.id == CHANNEL_ID)): return
    if m.from_user.id != ADMIN_ID: return await m.reply("❌ فقط ادمین میتونه فایل فوروارد کنه")
    if not m.document and not m.video: return await m.reply("❌ لطفاً یک فایل (PDF یا ویدیو) فوروارد کن")
    tags = re.findall(r'#([^#\s]+)', m.caption or "")
    if len(tags) < 5: return await m.reply("❌ کپشن باید حداقل ۵ هشتگ داشته باشه:\n#موسسه #پایه #رشته #درس #دبیر")
    inst, gr, ma, sub, teach = [t.replace("_", " ") for t in tags[:5]]
    sub = {"زیست":"زیست شناسی","علوم و فنون":"علوم و فنون ادبی","روانشناسی":"روان شناسی","دینی":"دین و زندگی","ادبیات":"فارسی"}.get(sub, sub)
    async for db in get_db():
        db.add(Archive(category="pdf" if m.document else "video", type="pdf" if m.document else "video", grade=gr, major=ma, institute=inst, subject=sub, teacher=teach, file_id=m.document.file_id if m.document else m.video.file_id, file_name=m.document.file_name if m.document else f"video_{m.message_id}.mp4", uploaded_by=m.from_user.id))
        await db.commit()
    await m.reply(f"✅ فایل با موفقیت ذخیره شد!\n📚 {inst} - {gr} - {ma} - {sub} - {teach}")

async def handle_buttons(m: types.Message):
    t, uid = m.text, m.from_user.id
    
    # 1. Check subscription
    if t != "🔙 برگشت به منو" and not await check_subscription(uid, m.bot): 
        return await send_join_message(m)
    
    # 2. Check back button
    if t == "🔙 برگشت به منو":
        if uid in upload_state: del upload_state[uid]
        return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
    
    # 3. CAPTION HANDLERS
    if uid in upload_state and upload_state[uid].get("step") == "waiting_for_caption_file":
        state = upload_state[uid]
        caption = t
        if caption == "❌ لغو":
            del upload_state[uid]
            return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
        
        async for db in get_db():
            db.add(Archive(
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
                uploaded_by=uid
            ))
            await db.commit()
        
        del upload_state[uid]
        return await m.answer(
            f"✅ ثبت شد!\n📚 {state['grade']} - {state['major']} - {state['institute']} - {state['subject']}\n👨‍🏫 {state.get('teacher','ندارد')}\n📄 {state['temp_file_name']}",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو")),
            parse_mode="Markdown"
        )

    if uid in upload_state and upload_state[uid].get("step") == "waiting_for_caption_book":
        state = upload_state[uid]
        caption = t
        if caption == "❌ لغو":
            del upload_state[uid]
            return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
        async for db in get_db():
            db.add(Archive(category="book", type="pdf", grade=state["grade"], major=state["major"], institute=state["publisher"], subject=state["subject"], file_id=state["temp_file_id"], file_name=state["temp_file_name"], caption=caption, uploaded_by=uid))
            await db.commit()
        del upload_state[uid]
        return await m.answer(
            f"✅ کتاب ثبت شد!\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو")),
            parse_mode="Markdown"
        )

    # 4. Check admin access
    if uid != ADMIN_ID and t in ["👑 پنل ادمین","⚡ آپلود سریع","📤 آپلود جزوه","🎥 آپلود ویدئو","📖 آپلود کتاب","🗑 حذف دبیر","➕ اضافه کردن انتشارات","📋 لیست فایل‌ها","🗑 حذف فایل","👥 لیست کاربران","📊 آمار","⚙️ تنظیمات","💾 بکاپ"]:
        return await m.answer("⛔ دسترسی نداری")
    
    # 5. Admin panel
    if t == "👑 پنل ادمین": 
        return await m.answer("👑 **پنل مدیریت**", reply_markup=admin_kb(), parse_mode="Markdown")
    
    # 6. Contact admin
    if t == "📩 ارتباط با ادمین":
        kb = types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("📩 ارسال پیام به ادمین", url="https://t.me/unbrokensociety2026"))
        await m.answer("📩 **ارتباط با ادمین**\n\nبرای ارتباط مستقیم با ادمین، روی دکمه زیر کلیک کن و پیامت رو بفرست.\n\n📌 پاسخ شما در اسرع وقت داده میشه.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")), parse_mode="Markdown")
        return await m.answer("👇 روی دکمه زیر کلیک کن:", reply_markup=kb)

    # ===================== DOWNLOAD =====================
    if t in ["📚 جزوه", "🎥 ویدئو"]:
        if uid in upload_state: del upload_state[uid]
        upload_state[uid] = {"mode": "user_download", "step": "grade", "category": "pdf" if t == "📚 جزوه" else "video"}
        return await m.answer("کدوم پایه؟", reply_markup=grade_keyboard())
    
    if t == "📖 کتاب کمک آموزشی":
        if uid in upload_state: del upload_state[uid]
        upload_state[uid] = {"mode": "user_download", "step": "book_grade", "category": "book"}
        return await m.answer("📖 **کتاب کمک آموزشی**\n\nکدوم پایه؟", reply_markup=await book_grade_keyboard())

    # ===================== UPLOAD =====================
    if t == "⚡ آپلود سریع":
        upload_state[uid] = {"mode": "fast_upload", "step": "waiting_for_file"}
        return await m.answer("⚡ **حالت آپلود سریع فعال شد!**\n\n📤 فایل رو بفرست و توی کپشن این اطلاعات رو بنویس:\n\n`نوع | موسسه/ناشر | پایه | رشته | درس | دبیر`\n\nمثال: `جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")), parse_mode="Markdown")
    
    if t == "📖 آپلود کتاب":
        upload_state[uid] = {"mode": "book_upload", "category": "book", "type": "pdf", "step": "book_publisher"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        [kb.add(KeyboardButton(p)) for p in ["فرمول بیست", "IQ", "نشر الگو", "خیلی سبز", "نردبام"]]
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("📖 **آپلود کتاب کمک آموزشی**\n\nناشر رو انتخاب کن:", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("mode") == "book_upload":
        state = upload_state[uid]
        if state.get("step") == "book_publisher":
            state["publisher"] = t
            state["step"] = "book_grade"
            return await m.answer(f"📖 ناشر: {t}\n\nپایه را انتخاب کن:", reply_markup=await book_grade_keyboard())
        if state.get("step") == "book_grade":
            state["grade"] = t
            state["step"] = "book_major"
            return await m.answer(
                f"📖 {state['publisher']} - {t}\n\nرشته را انتخاب کن:",
                reply_markup=major_keyboard(grade=t)
            )
        if state.get("step") == "book_major":
            state["major"] = t
            state["step"] = "book_subject"
            return await m.answer(
                f"📖 {state['publisher']} - {state['grade']} - {t}\n\nدرس مورد نظر رو انتخاب کن:",
                reply_markup=await book_subject_keyboard(state["publisher"], state["grade"], t)
            )
        if state.get("step") == "book_subject":
            state["subject"] = t
            state["step"] = "waiting_for_file"
            return await m.answer(
                f"✅ اطلاعات ثبت شد:\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}\n\n📤 حالا فایل رو ارسال کن (PDF)",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
            )

    if t in ["📤 آپلود جزوه", "🎥 آپلود ویدئو"]:
        upload_state[uid] = {"mode": "admin_upload", "category": "pdf" if t == "📤 آپلود جزوه" else "video", "type": "pdf" if t == "📤 آپلود جزوه" else "video", "step": "grade"}
        return await m.answer("پایه را انتخاب کن:", reply_markup=grade_keyboard())

    # ===================== GRADE/MAJOR/INSTITUTE FLOW =====================
    if t in ["دهم", "یازدهم", "دوازدهم", "جامع"]:
        if uid in upload_state:
            state = upload_state[uid]

            if state.get("step") == "book_grade":
                state["grade"] = t
                state["step"] = "book_major"
                return await m.answer(
                    f"📖 پایه: {t}\n\nرشته را انتخاب کن:",
                    reply_markup=major_keyboard(grade=t)
                )

            if state.get("mode") in ["admin_upload", "user_download"] and state.get("step") == "grade":
                state["grade"] = t
                state["step"] = "major"
                return await m.answer(
                    f"پایه: {t}\n\nرشته را انتخاب کن:",
                    reply_markup=major_keyboard(grade=t)
                )
    
    if t.startswith("رشته:"):
        if uid not in upload_state: return await m.answer("❌ لطفاً از ابتدا شروع کن")
        gr, ma = t.replace("رشته:", "").split("|")
        state = upload_state[uid]
        
        if state.get("mode") == "book_upload" and state.get("step") == "book_major":
            state["grade"] = gr
            state["major"] = ma
            state["step"] = "book_subject"
            return await m.answer(
                f"📖 {state['publisher']} - {gr} - {ma}\n\nدرس مورد نظر رو انتخاب کن:",
                reply_markup=await book_subject_keyboard(state["publisher"], gr, ma)
            )
        
        if state.get("mode") == "admin_upload" and state.get("step") == "major":
            state["grade"] = gr
            state["major"] = ma
            state["step"] = "institute"
            return await m.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
        
        if state.get("mode") == "user_download" and state.get("category") != "book" and state.get("step") == "major":
            state["grade"] = gr
            state["major"] = ma
            state["step"] = "institute"
            return await m.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())

    if uid in upload_state and upload_state[uid].get("step") == "institute":
        state = upload_state[uid]
        state["institute"] = t
        state["step"] = "subject"
        return await m.answer(
            f"🏛 موسسه: {t}\n\n📚 درس را انتخاب کن:",
            reply_markup=subject_keyboard(major=state.get("major", ""))
        )

    # ===================== SUBJECT HANDLER (with lazy import) =====================
    if uid in upload_state and upload_state[uid].get("step") == "subject":
        state = upload_state[uid]
        state["subject"] = t
        state["step"] = "teacher"
        if state.get("mode") in ["admin_upload", "user_download"]:
            from bot.data.teacher import teacher_keyboard  # ← Lazy import to fix circular import
            kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], t)
            if kb:
                kb.add(KeyboardButton("🔙 برگشت به منو"))
                return await m.answer("👨‍🏫 دبیر را انتخاب کن:", reply_markup=kb)
            return await m.answer("❌ دبیری برای این درس پیدا نشد.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")))

    if uid in upload_state and upload_state[uid].get("step") == "teacher":
        state = upload_state[uid]
        state["teacher"] = t
        
        if state.get("mode") == "admin_upload":
            state["step"] = "waiting_for_file"
            return await m.answer(
                f"✅ دبیر {t} انتخاب شد.\n\n📤 حالا فایل رو ارسال کن (PDF یا ویدیو)",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
            )
        
        if state.get("mode") == "user_download":
            return await show_archives(m, state)

    # ===================== OTHER ADMIN FUNCTIONS =====================
    if t == "🗑 حذف دبیر":
        upload_state[uid] = {"mode": "delete_teacher", "step": "ask_institute"}
        return await m.answer("🗑 **حذف دبیر**\n\nموسسه رو انتخاب کن:", reply_markup=await institute_keyboard())
    
    if uid in upload_state and upload_state[uid].get("mode") == "delete_teacher":
        state = upload_state[uid]
        if state.get("step") == "ask_institute":
            state["institute"] = t
            state["step"] = "ask_grade"
            return await m.answer(f"🏛 موسسه: {t}\n\nپایه رو انتخاب کن:", reply_markup=grade_keyboard())
        if state.get("step") == "ask_grade":
            state["grade"] = t
            state["step"] = "ask_major"
            return await m.answer(
                f"🏛 موسسه: {state['institute']}\n📚 پایه: {t}\n\nرشته رو انتخاب کن:",
                reply_markup=major_keyboard(grade=t)
            )
        if state.get("step") == "ask_major":
            if t.startswith("رشته:"):
                _, ma = t.replace("رشته:", "").split("|")
            else:
                ma = t
            state["major"] = ma
            state["step"] = "ask_teacher"
            
            async for db in get_db():
                pub = await db.scalar(select(Publisher).where(Publisher.name == state["institute"]))
                teachers = (await db.execute(select(Teacher).where(
                    Teacher.publisher_id == pub.id,
                    Teacher.grade == state["grade"],
                    Teacher.major == ma
                ))).scalars().all() if pub else []
            
            if not teachers:
                return await m.answer("❌ دبیری پیدا نشد.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")))
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            [kb.add(KeyboardButton(teacher.name)) for teacher in teachers]
            kb.add("❌ لغو")
            kb.add("🔙 برگشت به منو")
            state["teachers_list"] = {teacher.name: teacher.id for teacher in teachers}
            return await m.answer(
                f"🏛 موسسه: {state['institute']}\n📚 پایه: {state['grade']}\n🎓 رشته: {ma}\n\nدبیر مورد نظر برای حذف رو انتخاب کن:",
                reply_markup=kb
            )
        if state.get("step") == "ask_teacher":
            if t in ["❌ لغو", "🔙 برگشت به منو"]:
                del upload_state[uid]
                return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
            tid = state.get("teachers_list", {}).get(t)
            if not tid:
                return await m.answer("❌ دبیر پیدا نشد")
            async for db in get_db():
                teacher = await db.scalar(select(Teacher).where(Teacher.id == tid))
                if teacher:
                    await db.delete(teacher)
                    await db.commit()
            await m.answer(f"✅ دبیر {t} با موفقیت حذف شد!")
            del upload_state[uid]
            return await m.answer("👑 پنل مدیریت", reply_markup=admin_kb())

    if t == "➕ اضافه کردن انتشارات":
        upload_state[uid] = {"mode": "add_publisher", "step": "ask_name"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("📝 **اضافه کردن انتشارات جدید**\n\nنام انتشارات رو وارد کن:\n(مثال: ماجرای ۲۰)\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)

    if uid in upload_state and upload_state[uid].get("mode") == "add_publisher":
        state = upload_state[uid]
        if state.get("step") == "ask_name":
            state["name"] = t
            state["step"] = "ask_type"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("موسسه آموزشی")
            kb.add("ناشر کتاب")
            kb.add("🔙 برگشت به منو")
            return await m.answer(f"نوع انتشارات رو انتخاب کن:\n\n📌 {t}\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_type":
            state["pub_type"] = "institute" if t == "موسسه آموزشی" else "book_publisher"
            state["step"] = "ask_grade"
            state["subjects_data"] = {}
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("دهم")
            kb.add("یازدهم")
            kb.add("دوازدهم")
            kb.add("🔙 برگشت به منو")
            return await m.answer(f"📌 **{state['name']}**\n\nپایه را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_grade":
            state["current_grade"] = t
            state["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("ریاضی")
            kb.add("تجربی")
            kb.add("🔙 برگشت به منو")
            return await m.answer(f"📌 **{state['name']}**\n📚 پایه: {t}\n\nرشته را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_major":
            state["current_major"] = t
            state["step"] = "ask_subject"
            state["temp_subjects"] = []
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("✅ ثبت دروس"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"📌 **{state['name']}**\n📚 پایه: {state['current_grade']}\n🎓 رشته: {t}\n\nدروس مربوط به این رشته رو وارد کن.\nهر درس رو در یه خط جداگانه بنویس.\n\nمثال:\nفیزیک\nشیمی\nریاضی\n\n⚠️ وقتی تموم شد، روی دکمه **✅ ثبت دروس** بزن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_subject":
            if t == "✅ ثبت نهایی":
                if not state.get("subjects_data", {}):
                    return await m.answer("❌ حداقل برای یک پایه درس وارد کن!")
                async for db in get_db():
                    if await db.scalar(select(Publisher).where(Publisher.name == state["name"])):
                        return await m.answer(f"❌ انتشارات {state['name']} قبلاً وجود داره!")
                    db.add(Publisher(name=state["name"], type=state["pub_type"], subjects_by_grade=state["subjects_data"]))
                    await db.commit()
                del upload_state[uid]
                text = f"✅ انتشارات {state['name']} با موفقیت اضافه شد!\n\n📚 دروس ثبت شده:\n"
                for g, data in state["subjects_data"].items():
                    text += f"   • {g}:\n"
                    for m, s in data.items():
                        text += f"      - {m}: {', '.join(s)}\n"
                return await m.answer(text, reply_markup=await main_menu(uid))
            if t == "✅ ثبت دروس":
                if not state.get("temp_subjects", []):
                    return await m.answer(f"❌ حداقل یک درس وارد کن!")
                g, m = state["current_grade"], state["current_major"]
                if "subjects_data" not in state:
                    state["subjects_data"] = {}
                if g not in state["subjects_data"]:
                    state["subjects_data"][g] = {}
                state["subjects_data"][g][m] = state["temp_subjects"]
                state["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("دهم")
                kb.add("یازدهم")
                kb.add("دوازدهم")
                kb.add("✅ ثبت نهایی")
                kb.add("🔙 برگشت به منو")
                text = f"✅ دروس {m} برای پایه {g} ثبت شد.\n\n📚 لیست فعلی:\n"
                for g2, data in state["subjects_data"].items():
                    text += f"   • {g2}:\n"
                    for m2, s in data.items():
                        text += f"      - {m2}: {', '.join(s)}\n"
                text += "\nبرای ادامه، پایه دیگه رو انتخاب کن یا روی **✅ ثبت نهایی** بزن."
                return await m.answer(text, reply_markup=kb)
            if t == "🔙 برگشت به منو":
                del upload_state[uid]
                return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
            if "temp_subjects" not in state:
                state["temp_subjects"] = []
            new = [s.strip() for s in t.split("\n") if s.strip()]
            added = [s for s in new if s not in state["temp_subjects"]]
            state["temp_subjects"].extend(added)
            if added:
                text = f"✅ {len(added)} درس اضافه شد:\n" + "\n".join([f"   • {s}" for s in added])
                text += f"\n\n📚 لیست فعلی:\n" + "\n".join([f"   • {s}" for s in state["temp_subjects"]])
                return await m.answer(text)
            return await m.answer("⚠️ هیچ درس جدیدی اضافه نشد (همه تکراری بودن)")

    if t == "👥 لیست کاربران": return await list_users(m)
    if t == "⚙️ تنظیمات":
        return await m.answer(
            "⚙️ **پنل تنظیمات**\n\n🔹 تغییر ادمین: آیدی جدید رو وارد کن\n🔹 پیام همگانی: به همه کاربران پیام بفرست\n\n⚠️ **توجه:** این تنظیمات فقط برای ادمین قابل دسترسه.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 تغییر ادمین").add("📢 پیام همگانی").add("🔙 برگشت به منو"),
            parse_mode="Markdown"
        )
    if t == "💾 بکاپ": return await backup_database(m)
    if t == "📢 پیام همگانی":
        upload_state[uid] = {"mode": "broadcast", "step": "waiting_for_message"}
        return await m.answer(
            "📢 **ارسال پیام همگانی**\n\nپیام مورد نظر رو وارد کن:\n\n⚠️ این پیام به **همه کاربران** ارسال میشه.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ لغو").add("🔙 برگشت به منو")
        )
    if uid in upload_state and upload_state[uid].get("mode") == "broadcast" and upload_state[uid].get("step") == "waiting_for_message":
        if t in ["❌ لغو", "🔙 برگشت به منو"]:
            del upload_state[uid]
            return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
        await m.answer("⏳ **در حال ارسال پیام به کاربران...**")
        try:
            async for db in get_db():
                users = (await db.execute(select(User))).scalars().all()
            sent = 0
            for user in users:
                try:
                    await m.bot.send_message(user.telegram_id, f"📢 **پیام همگانی**\n\n{t}", parse_mode="Markdown")
                    sent += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            await m.answer(f"✅ **پیام همگانی ارسال شد!**\n\n📤 ارسال شده: {sent}\n👥 کل کاربران: {len(users)}")
        except Exception as e:
            await m.answer(f"❌ خطا: `{str(e)}`", parse_mode="Markdown")
        del upload_state[uid]
        return await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(uid))
    
    if t == "❌ لغو":
        if uid in upload_state: del upload_state[uid]
        return await m.answer("❌ آپلود لغو شد", reply_markup=await main_menu(uid))
    if t == "📋 لیست فایل‌ها": return await list_files(m)
    if t == "🗑 حذف فایل":
        upload_state[uid] = {"mode": "admin_delete", "step": "waiting_for_file_id"}
        return await m.answer(
            "🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")),
            parse_mode="Markdown"
        )
    if uid in upload_state and upload_state[uid].get("mode") == "admin_delete":
        return await delete_file(m, t)
    if t == "📊 آمار": return await show_stats(m)
    if t == "⚡ ادامه" and uid in upload_state:
        state = upload_state[uid]
        state["step"] = "waiting_for_file"
        return await m.answer(
            "📤 فایل بعدی رو بفرست.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        )

async def list_users(m: types.Message, page=1):
    per_page = 10
    async for db in get_db():
        total = await db.scalar(select(func.count()).select_from(User))
        users = (await db.execute(select(User).order_by(User.id.desc()).offset((page-1)*per_page).limit(per_page))).scalars().all()
    if not users: return await m.answer("❌ هیچ کاربری وجود ندارد")
    text = f"👥 **لیست کاربران** (صفحه {page})\n\n📊 **تعداد کل:** {total}\n\n"
    for i, u in enumerate(users, start=(page-1)*per_page+1):
        text += f"{i}. {u.full_name} - @{u.username or 'ندارد'}\n   🆔 {u.telegram_id}\n"
    kb = types.InlineKeyboardMarkup(row_width=2)
    if page > 1: kb.insert(types.InlineKeyboardButton("◀️ قبلی", callback_data=f"users_page_{page-1}"))
    if page*per_page < total: kb.insert(types.InlineKeyboardButton("▶️ بعدی", callback_data=f"users_page_{page+1}"))
    await m.answer(text, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")), parse_mode="Markdown")
    if kb.inline_keyboard: await m.answer("📌 برای رفتن به صفحه بعد/قبل از دکمه‌های زیر استفاده کن:", reply_markup=kb)

async def backup_database(m: types.Message):
    async for db in get_db():
        uc = await db.scalar(select(func.count()).select_from(User))
        fc = await db.scalar(select(func.count()).select_from(Archive))
        pc = await db.scalar(select(func.count()).select_from(Publisher))
        tc = await db.scalar(select(func.count()).select_from(Teacher))
    await m.answer(
        f"📊 **گزارش بکاپ دیتابیس**\n\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n👥 کاربران: {uc}\n📄 فایل‌ها: {fc}\n🏛 انتشارات: {pc}\n👨‍🏫 دبیران: {tc}",
        parse_mode="Markdown"
    )
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def show_stats(m: types.Message):
    async for db in get_db():
        uc = await db.scalar(select(func.count()).select_from(User))
        fc = await db.scalar(select(func.count()).select_from(Archive))
        pdf = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category=="pdf"))
        vid = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category=="video"))
        bk = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category=="book"))
    await m.answer(
        f"📊 **آمار ربات**\n\n👥 کاربران: {uc}\n📄 کل فایل‌ها: {fc}\n📁 جزوه: {pdf}\n🎥 ویدیو: {vid}\n📖 کتاب: {bk}",
        parse_mode="Markdown"
    )
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def list_files(m: types.Message):
    async for db in get_db():
        files = (await db.execute(select(Archive).order_by(Archive.id.desc()).limit(20))).scalars().all()
    if not files: return await m.answer("❌ هیچ فایلی وجود ندارد")
    for f in files:
        cat = {"pdf":"📄 جزوه","video":"🎥 ویدیو","book":"📖 کتاب"}.get(f.category,"📄")
        await m.answer(
            f"{cat} **{f.file_name}**\n\n🆔 `{f.file_id[:20]}...`\n📚 پایه: {f.grade}\n🎓 رشته: {f.major}\n🏛 موسسه: {f.institute}\n📖 درس: {f.subject}\n👨‍🏫 دبیر: {f.teacher or 'ندارد'}",
            parse_mode="Markdown"
        )
    await m.answer(f"✅ {len(files)} فایل آخر نمایش داده شد")

async def delete_file(m: types.Message, file_id: str):
    async for db in get_db():
        file = await db.scalar(select(Archive).where(Archive.file_id.like(f"%{file_id}%")))
        if file:
            await db.delete(file)
            await db.commit()
            await m.answer(f"✅ فایل حذف شد:\n\n📄 {file.file_name}")
        else:
            await m.answer(f"❌ فایلی با آیدی `{file_id}` پیدا نشد")
    if m.from_user.id in upload_state: del upload_state[m.from_user.id]
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def show_book_archives(m: types.Message, state: dict):
    async for db in get_db():
        archives = (await db.execute(select(Archive).where(
            Archive.category=="book",
            Archive.grade==state["grade"],
            Archive.major==state["major"],
            Archive.institute==state["publisher"],
            Archive.subject==state["subject"]
        ))).scalars().all()
    if not archives:
        return await m.answer("❌ هیچ کتابی پیدا نشد", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")))
    for a in archives:
        await send_file_with_timer(m.bot, m.from_user.id, a.file_id, f"📖 {a.file_name}\n" + (f"📝 {a.caption}\n" if a.caption else ""))
    if m.from_user.id in upload_state: del upload_state[m.from_user.id]
    await m.answer("✅ همه کتاب‌ها ارسال شد", reply_markup=await main_menu(m.from_user.id))

async def show_archives(m: types.Message, state: dict):
    archives = []
    async for db in get_db():
        archives = (await db.execute(select(Archive).where(
            Archive.teacher == state["teacher"],
            Archive.grade == state["grade"],
            Archive.major == state["major"],
            Archive.institute == state["institute"],
            Archive.subject == state["subject"]
        ))).scalars().all()
    
    if not archives:
        return await m.answer("❌ هیچ فایلی برای این دبیر پیدا نشد", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو")))
    
    for a in archives:
        is_video = a.type == "video" or (a.file_name and a.file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')))
        cap = f"📄 {a.file_name}" + (f"\n📝 {a.caption}" if a.caption else "")
        await send_file_with_timer(m.bot, m.from_user.id, a.file_id, cap, is_video=is_video)
    
    if m.from_user.id in upload_state: del upload_state[m.from_user.id]
    await m.answer("✅ همه فایل‌ها ارسال شد", reply_markup=await main_menu(m.from_user.id))

async def handle_file(m: types.Message):
    uid = m.from_user.id
    if m.chat.id == CHANNEL_ID or (m.forward_from_chat and m.forward_from_chat.id == CHANNEL_ID):
        return await auto_save_from_channel(m)
    if uid not in upload_state:
        return await m.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
    state = upload_state[uid]

    if state.get("mode") == "fast_upload":
        parts = [p.strip() for p in (m.caption or "").split("|")]
        if len(parts) < 5:
            return await m.answer("❌ فرمت کپشن اشتباهه!\n\nمثال: `جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`", parse_mode="Markdown")
        cat, inst, gr, ma, sub = parts[:5]
        teach, bn = parts[5] if len(parts)>5 else None, parts[6] if len(parts)>6 else None
        async for db in get_db():
            db.add(Archive(
                category={"جزوه":"pdf","ویدیو":"video","کتاب":"book"}.get(cat,"pdf"),
                type="pdf" if m.document else "video",
                grade=gr,
                major=ma,
                institute=inst,
                subject=sub,
                teacher=teach,
                book_name=bn,
                file_id=m.document.file_id if m.document else m.video.file_id,
                file_name=m.document.file_name if m.document else f"video_{m.message_id}.mp4",
                uploaded_by=uid
            ))
            await db.commit()
        return await m.answer(
            f"✅ فایل ثبت شد!\n📚 {inst} - {gr} - {ma} - {sub}",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        )

    if state.get("mode") == "book_upload" and state.get("step") == "waiting_for_file":
        if not m.document:
            return await m.answer("❌ لطفاً فایل PDF کتاب رو ارسال کن")
        state["temp_file_id"] = m.document.file_id
        state["temp_file_name"] = m.document.file_name or "unknown.pdf"
        state["step"] = "waiting_for_caption_book"
        return await m.answer(
            f"✅ فایل کتاب دریافت شد!\n📄 {state['temp_file_name']}\n\n📝 حالا کپشن کتاب رو وارد کن:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        )

    if state.get("mode") == "admin_upload" and state.get("step") == "waiting_for_file":
        if not m.document and not m.video:
            return await m.answer("❌ لطفاً فقط فایل PDF یا ویدیو ارسال کن")
        state["temp_file_id"] = m.document.file_id if m.document else m.video.file_id
        state["temp_file_name"] = m.document.file_name if m.document else f"video_{m.video.file_id[:8]}.mp4"
        state["temp_file_type"] = "pdf" if m.document else "video"
        state["step"] = "waiting_for_caption_file"
        return await m.answer(
            f"✅ فایل دریافت شد!\n📄 {state['temp_file_name']}\n\n📝 حالا کپشن فایل رو وارد کن:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        )

async def handle_callback(cb: types.CallbackQuery):
    await cb.answer()
    
    if cb.data == "back_to_menu":
        await cb.message.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(cb.from_user.id))
        await cb.message.delete()
        return
    
    if cb.data.startswith("users_page_"):
        page = int(cb.data.split("_")[2])
        class Mock:
            def __init__(self, c):
                self.from_user = c.from_user
                self.bot = c.bot
                self.chat = c.message.chat
                self.message_id = c.message.message_id
                self.text = f"users_page_{page}"
            async def answer(self, *args, **kwargs):
                return await cb.message.answer(*args, **kwargs)
        await list_users(Mock(cb), page)
        return

def register_handlers(dp):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(handle_file, content_types=["document", "video"])
    dp.register_message_handler(handle_buttons, content_types=["text"])
    dp.register_callback_query_handler(handle_callback, lambda c: True)
