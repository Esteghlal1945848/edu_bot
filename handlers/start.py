from aiogram import types
from sqlalchemy import select, func
from database.core import get_db
from database.models import User, Archive, Publisher, Teacher, Session
from bot.keyboards.archive import (
    grade_keyboard, major_keyboard, institute_keyboard, publisher_keyboard,
    subject_keyboard, book_subject_keyboard, book_publisher_keyboard, book_grade_keyboard,
)
from bot.data.teacher import teacher_keyboard
from handlers.state import upload_state
from aiogram.types import KeyboardButton
import re, asyncio
from datetime import datetime

ADMIN_ID = 7336595194
CHANNEL_ID = -1002505515904
CHANNEL_LINK = "https://t.me/School_learny"

# ========================= helper =========================
async def main_menu(user_id: int):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = ["📚 جزوه", "🎥 ویدئو", "📖 کتاب کمک آموزشی", "📩 ارتباط با ادمین"]
    kb.add(*[KeyboardButton(b) for b in btns])
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

# ========================= ارسال فایل با تایمر =========================
async def send_file_with_timer(bot, chat_id, file_id, caption="", delay=30):
    sent_file = await bot.send_document(chat_id, file_id, caption=caption)
    timer_msg = await bot.send_message(
        chat_id,
        f"⏳ **این فایل تا {delay} ثانیه دیگه پاک میشه!**\n\n⬇️ لطفاً سریع دانلود کنید.\n\n🕐 {delay} ثانیه مهلت دارید.",
        parse_mode="Markdown"
    )
    async def delete_timer_and_file():
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id, timer_msg.message_id)
            await bot.delete_message(chat_id, sent_file.message_id)
        except:
            pass
    asyncio.create_task(delete_timer_and_file())
    return sent_file

def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row1 = ["⚡ آپلود سریع", "📤 آپلود جزوه", "🎥 آپلود ویدئو", "📖 آپلود کتاب"]
    row2 = ["📤 آپلود جلسه", "🗑 حذف دبیر", "➕ اضافه کردن انتشارات"]
    row3 = ["📋 لیست فایل‌ها", "🗑 حذف فایل"]
    row4 = ["👥 لیست کاربران", "📊 آمار"]
    row5 = ["⚙️ تنظیمات", "💾 بکاپ", "🔙 برگشت به منو"]
    kb.add(*[KeyboardButton(b) for b in row1]); kb.add(*[KeyboardButton(b) for b in row2]); kb.add(*[KeyboardButton(b) for b in row3]); kb.add(*[KeyboardButton(b) for b in row4]); kb.add(*[KeyboardButton(b) for b in row5])
    return kb

# ========================= START =========================
async def cmd_start(m: types.Message):
    if not await check_subscription(m.from_user.id, m.bot): return await send_join_message(m)
    kb = await main_menu(m.from_user.id)
    await m.answer(
        "🎓 **به بزرگترین آرشیو آموزشی خوش آمدید!**\n\n"
        "📚 **سالیانه‌های ۱۴۰۶ در دسترس قرار گرفت!**\n"
        "✅ **کلاس‌های آلفا اسکول شروع شد!**\n\n"
        "🔹 برای مشاهده جزوه‌ها، دکمه **📚 جزوه** رو بزن\n"
        "🔹 برای مشاهده ویدیوها، دکمه **🎥 ویدئو** رو بزن\n"
        "🔹 برای مشاهده کتاب‌های کمک آموزشی، دکمه **📖 کتاب کمک آموزشی** رو بزن\n\n"
        "💡 **نکته:** برای برگشت از هر مرحله‌ای، روی دکمه **🔙 برگشت به منو** کلیک کن یا دستور **/start** رو بزن.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    async for db in get_db():
        r = await db.execute(select(User).where(User.telegram_id == m.from_user.id))
        if not r.scalar_one_or_none(): db.add(User(telegram_id=m.from_user.id, username=m.from_user.username, full_name=m.from_user.full_name)); await db.commit()

async def auto_save_from_channel(m: types.Message):
    if not (m.chat.id == CHANNEL_ID or (m.forward_from_chat and m.forward_from_chat.id == CHANNEL_ID)): return
    if m.from_user.id != ADMIN_ID: return await m.reply("❌ فقط ادمین میتونه فایل فوروارد کنه")
    if not m.document and not m.video: return await m.reply("❌ لطفاً یک فایل (PDF یا ویدیو) فوروارد کن")
    tags = re.findall(r'#([^#\s]+)', m.caption or "")
    if len(tags) < 5: return await m.reply("❌ کپشن باید حداقل ۵ هشتگ داشته باشه:\n#موسسه #پایه #رشته #درس #دبیر\n\nمثال: #تایتان #دهم #ریاضی #شیمی #فراهانی")
    inst, gr, ma, sub, teach = [t.replace("_", " ") for t in tags[:5]]
    sub = {"زیست":"زیست شناسی","علوم و فنون":"علوم و فنون ادبی","روانشناسی":"روان شناسی","دینی":"دین و زندگی","ادبیات":"فارسی"}.get(sub, sub)
    async for db in get_db():
        db.add(Archive(category="pdf" if m.document else "video", type="pdf" if m.document else "video", grade=gr, major=ma, institute=inst, subject=sub, teacher=teach, file_id=m.document.file_id if m.document else m.video.file_id, file_name=m.document.file_name if m.document else f"video_{m.message_id}.mp4", uploaded_by=m.from_user.id))
        await db.commit()
    await m.reply(f"✅ فایل با موفقیت ذخیره شد!\n📚 {inst} - {gr} - {ma} - {sub} - {teach}")

# ========================= HANDLE BUTTONS =========================
async def handle_buttons(m: types.Message):
    t, uid = m.text, m.from_user.id
    if t != "🔙 برگشت به منو" and not await check_subscription(uid, m.bot): return await send_join_message(m)
    if t == "🔙 برگشت به منو":
        if uid in upload_state: del upload_state[uid]
        return await m.answer("🔙 به منوی اصلی برگشتی.\n\n💡 **نکته:** برای برگشت از هر مرحله‌ای، روی دکمه **🔙 برگشت به منو** کلیک کن یا دستور **/start** رو بزن.", reply_markup=await main_menu(uid))
    
    if uid != ADMIN_ID and t in ["👑 پنل ادمین","⚡ آپلود سریع","📤 آپلود جزوه","🎥 آپلود ویدئو","📖 آپلود کتاب","📤 آپلود جلسه","🗑 حذف دبیر","➕ اضافه کردن انتشارات","📋 لیست فایل‌ها","🗑 حذف فایل","👥 لیست کاربران","📊 آمار","⚙️ تنظیمات","💾 بکاپ"]:
        return await m.answer("⛔ دسترسی نداری")
    
    if t == "👑 پنل ادمین": return await m.answer("👑 **پنل مدیریت**", reply_markup=admin_kb(), parse_mode="Markdown")
    if t == "📩 ارتباط با ادمین":
        kb = types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("📩 ارسال پیام به ادمین", url="https://t.me/unbrokensociety2026"))
        back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        await m.answer("📩 **ارتباط با ادمین**\n\nبرای ارتباط مستقیم با ادمین، روی دکمه زیر کلیک کن و پیامت رو بفرست.\n\n📌 پاسخ شما در اسرع وقت داده میشه.", reply_markup=back_kb, parse_mode="Markdown")
        return await m.answer("👇 روی دکمه زیر کلیک کن:", reply_markup=kb)
    
    # ===================== آپلود جلسه (ادمین) =====================
    if t == "📤 آپلود جلسه":
        upload_state[uid] = {"mode": "session_upload", "step": "ask_teacher"}
        await m.answer(
            "📤 **آپلود جلسه جدید**\n\n"
            "نام دبیر رو وارد کن:\n"
            "مثال: معین کرمی\n\n"
            "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        )
        return
    
    if uid in upload_state and upload_state[uid].get("mode") == "session_upload":
        state = upload_state[uid]
        if state.get("step") == "ask_teacher":
            state["teacher_name"] = t
            state["step"] = "ask_grade"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
            kb.add(KeyboardButton("دوازدهم"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"👨‍🏫 دبیر: {t}\n\nپایه رو انتخاب کن:", reply_markup=kb)
        
        if state.get("step") == "ask_grade":
            state["grade"] = t
            state["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("ریاضی"))
            kb.add(KeyboardButton("تجربی"))
            kb.add(KeyboardButton("انسانی"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"👨‍🏫 دبیر: {state['teacher_name']}\n📚 پایه: {t}\n\nرشته رو انتخاب کن:", reply_markup=kb)
        
        if state.get("step") == "ask_major":
            state["major"] = t
            state["step"] = "ask_subject"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subjects.get(t, []):
                kb.add(KeyboardButton(s))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"👨‍🏫 دبیر: {state['teacher_name']}\n📚 پایه: {state['grade']}\n🎓 رشته: {t}\n\nدرس رو انتخاب کن:", reply_markup=kb)
        
        if state.get("step") == "ask_subject":
            state["subject"] = t
            state["step"] = "ask_institute"
            await m.answer(
                f"👨‍🏫 دبیر: {state['teacher_name']}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {state['major']}\n"
                f"📖 درس: {t}\n\n"
                "موسسه رو انتخاب کن:",
                reply_markup=await institute_keyboard()
            )
            return
        
        if state.get("step") == "ask_institute":
            state["institute"] = t
            state["step"] = "ask_session_number"
            await m.answer(
                f"👨‍🏫 دبیر: {state['teacher_name']}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {state['major']}\n"
                f"📖 درس: {state['subject']}\n"
                f"🏛 موسسه: {t}\n\n"
                "شماره جلسه رو وارد کن (مثلاً 1 یا 2):\n\n"
                "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
            )
            return
        
        if state.get("step") == "ask_session_number":
            try:
                session_num = int(t)
            except:
                return await m.answer("❌ لطفاً یک عدد معتبر وارد کن")
            
            # پیدا کردن دبیر
            async for db in get_db():
                pub = await db.scalar(select(Publisher).where(Publisher.name == state["institute"]))
                if not pub:
                    return await m.answer("❌ موسسه پیدا نشد")
                teacher = await db.scalar(
                    select(Teacher).where(
                        Teacher.name == state["teacher_name"],
                        Teacher.publisher_id == pub.id,
                        Teacher.grade == state["grade"],
                        Teacher.major == state["major"],
                        Teacher.subject == state["subject"]
                    )
                )
                if not teacher:
                    return await m.answer("❌ دبیر پیدا نشد")
                state["teacher_id"] = teacher.id
            
            state["session_number"] = session_num
            state["step"] = "waiting_for_file"
            
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("❌ لغو"))
            kb.add(KeyboardButton("🔙 برگشت به منو"))
            
            await m.answer(
                f"✅ اطلاعات ثبت شد:\n"
                f"👨‍🏫 {state['teacher_name']}\n"
                f"📚 جلسه {session_num}\n\n"
                f"📤 حالا فایل جلسه رو ارسال کن (PDF یا ویدیو)",
                reply_markup=kb
            )
            return

    # ===================== دانلود جزوه/ویدیو =====================
    if t in ["📚 جزوه", "🎥 ویدئو"]:
        if uid in upload_state: del upload_state[uid]
        upload_state[uid] = {"mode": "user_download", "step": "grade", "category": "pdf" if t == "📚 جزوه" else "video"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم")); kb.add(KeyboardButton("دوازدهم")); kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("کدوم پایه؟\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if t == "⚡ آپلود سریع":
        upload_state[uid] = {"mode": "fast_upload", "step": "waiting_for_file"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("⚡ **حالت آپلود سریع فعال شد!**\n\n📤 فایل رو بفرست و توی کپشن این اطلاعات رو بنویس:\n\n`نوع | موسسه/ناشر | پایه | رشته | درس | دبیر`\n\nمثال برای جزوه:\n`جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`\n\nمثال برای کتاب:\n`کتاب | خیلی سبز | دهم | ریاضی | فیزیک | نردبام`\n\n⚠️ بین اطلاعات فقط `|` بذار\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb, parse_mode="Markdown")
    
    if t == "📖 آپلود کتاب":
        upload_state[uid] = {"mode": "book_upload", "category": "book", "type": "pdf", "step": "book_publisher"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for p in ["فرمول بیست", "IQ", "نشر الگو", "خیلی سبز", "نردبام"]: kb.add(KeyboardButton(p))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("📖 **آپلود کتاب کمک آموزشی**\n\nناشر رو انتخاب کن:", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("mode") == "book_upload" and upload_state[uid].get("step") == "book_publisher":
        upload_state[uid]["publisher"] = t
        upload_state[uid]["step"] = "book_grade"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم"))
        kb.row(KeyboardButton("دوازدهم"), KeyboardButton("جامع"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"📖 ناشر: {t}\n\nپایه را انتخاب کن:", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("mode") == "book_upload" and upload_state[uid].get("step") == "book_grade":
        upload_state[uid]["grade"] = t
        upload_state[uid]["step"] = "book_major"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton(f"رشته:{t}|ریاضی"))
        kb.add(KeyboardButton(f"رشته:{t}|تجربی"))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"📖 {upload_state[uid]['publisher']} - {t}\n\nرشته را انتخاب کن:", reply_markup=kb)
    
    if t in ["📤 آپلود جزوه", "🎥 آپلود ویدئو"]:
        upload_state[uid] = {"mode": "admin_upload", "category": "pdf" if t == "📤 آپلود جزوه" else "video", "type": "pdf" if t == "📤 آپلود جزوه" else "video", "step": "grade"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم")); kb.add(KeyboardButton("دوازدهم")); kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("پایه را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if t == "📖 کتاب کمک آموزشی":
        if uid in upload_state: del upload_state[uid]
        upload_state[uid] = {"mode": "user_download", "step": "book_grade", "category": "book"}
        return await m.answer("📖 **کتاب کمک آموزشی**\n\nکدوم پایه؟\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=await book_grade_keyboard())
    
    if t == "➕ اضافه کردن انتشارات":
        upload_state[uid] = {"mode": "add_publisher", "step": "ask_name"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("📝 **اضافه کردن انتشارات جدید**\n\nنام انتشارات رو وارد کن:\n(مثال: ماجرای ۲۰)\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("mode") == "add_publisher":
        state = upload_state[uid]
        if state.get("step") == "ask_name":
            state["name"] = t; state["step"] = "ask_type"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("موسسه آموزشی"); kb.add("ناشر کتاب"); kb.add("🔙 برگشت به منو")
            return await m.answer(f"نوع انتشارات رو انتخاب کن:\n\n📌 {t}\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_type":
            state["pub_type"] = "institute" if t == "موسسه آموزشی" else "book_publisher"
            state["step"] = "ask_grade"; state["subjects_data"] = {}
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("دهم"); kb.add("یازدهم"); kb.add("دوازدهم"); kb.add("🔙 برگشت به منو")
            return await m.answer(f"📌 **{state['name']}**\n\nپایه را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_grade":
            state["current_grade"] = t; state["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("ریاضی"); kb.add("تجربی"); kb.add("🔙 برگشت به منو")
            return await m.answer(f"📌 **{state['name']}**\n📚 پایه: {t}\n\nرشته را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_major":
            state["current_major"] = t; state["step"] = "ask_subject"; state["temp_subjects"] = []
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("✅ ثبت دروس")).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"📌 **{state['name']}**\n📚 پایه: {state['current_grade']}\n🎓 رشته: {t}\n\nدروس مربوط به این رشته رو وارد کن.\nهر درس رو در یه خط جداگانه بنویس.\n\nمثال:\nفیزیک\nشیمی\nریاضی\n\n⚠️ وقتی تموم شد، روی دکمه **✅ ثبت دروس** بزن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_subject":
            if t == "✅ ثبت نهایی":
                if not state.get("subjects_data", {}): return await m.answer("❌ حداقل برای یک پایه درس وارد کن!")
                async for db in get_db():
                    if await db.scalar(select(Publisher).where(Publisher.name == state["name"])): return await m.answer(f"❌ انتشارات {state['name']} قبلاً وجود داره!")
                    db.add(Publisher(name=state["name"], type=state["pub_type"], subjects_by_grade=state["subjects_data"])); await db.commit()
                del upload_state[uid]
                return await m.answer(f"✅ انتشارات {state['name']} با موفقیت اضافه شد!\n\n📚 دروس ثبت شده:\n" + "\n".join([f"   • {g}: " + "\n".join([f"      - {m}: {', '.join(s)}" for m,s in data.items()]) for g,data in state["subjects_data"].items()]), reply_markup=await main_menu(uid))
            if t == "✅ ثبت دروس":
                if not state.get("temp_subjects", []): return await m.answer(f"❌ حداقل یک درس وارد کن!")
                g, m = state["current_grade"], state["current_major"]
                if "subjects_data" not in state: state["subjects_data"] = {}
                if g not in state["subjects_data"]: state["subjects_data"][g] = {}
                state["subjects_data"][g][m] = state["temp_subjects"]
                state["temp_subjects"] = []
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("دهم"); kb.add("یازدهم"); kb.add("دوازدهم"); kb.add("✅ ثبت نهایی"); kb.add("🔙 برگشت به منو")
                return await m.answer(f"✅ دروس {m} برای پایه {g} ثبت شد.\n\n📚 لیست فعلی:\n" + "\n".join([f"   • {g2}: " + "\n".join([f"      - {m2}: {', '.join(s)}" for m2,s in data.items()]) for g2,data in state["subjects_data"].items()]) + "\n\nبرای ادامه، پایه دیگه رو انتخاب کن یا روی **✅ ثبت نهایی** بزن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
            if t == "🔙 برگشت به منو": del upload_state[uid]; return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
            if "temp_subjects" not in state: state["temp_subjects"] = []
            new = [s.strip() for s in t.split("\n") if s.strip()]
            added = [s for s in new if s not in state["temp_subjects"]]
            state["temp_subjects"].extend(added)
            if added: return await m.answer(f"✅ {len(added)} درس اضافه شد:\n" + "\n".join([f"   • {s}" for s in added]) + f"\n\n📚 لیست فعلی:\n" + "\n".join([f"   • {s}" for s in state["temp_subjects"]]))
            return await m.answer("⚠️ هیچ درس جدیدی اضافه نشد (همه تکراری بودن)")
    
    # ===================== GRADE =====================
    if t in ["دهم", "یازدهم", "دوازدهم", "جامع"]:
        if uid in upload_state and upload_state[uid].get("step") == "book_grade":
            upload_state[uid]["grade"] = t; upload_state[uid]["step"] = "book_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{t}|ریاضی")); kb.add(KeyboardButton(f"رشته:{t}|تجربی")); kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"📖 پایه: {t}\n\nرشته را انتخاب کن:", reply_markup=kb)
        
        if uid in upload_state and upload_state[uid].get("mode") == "admin_upload":
            upload_state[uid]["grade"] = t; upload_state[uid]["step"] = "major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{t}|ریاضی")); kb.add(KeyboardButton(f"رشته:{t}|تجربی")); kb.add(KeyboardButton(f"رشته:{t}|انسانی")); kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("رشته را انتخاب کن:", reply_markup=kb)
        
        if uid in upload_state and upload_state[uid].get("mode") == "user_download" and upload_state[uid].get("step") == "grade":
            upload_state[uid]["grade"] = t; upload_state[uid]["step"] = "major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{t}|ریاضی")); kb.add(KeyboardButton(f"رشته:{t}|تجربی")); kb.add(KeyboardButton(f"رشته:{t}|انسانی")); kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("رشته را انتخاب کن:", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("mode") == "book_upload" and upload_state[uid].get("step") == "publisher":
        upload_state[uid]["publisher"] = t; upload_state[uid]["step"] = "grade"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.row(KeyboardButton("دهم"), KeyboardButton("یازدهم")); kb.add(KeyboardButton("دوازدهم")); kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("پایه را انتخاب کن:", reply_markup=kb)
    
    if t.startswith("رشته:"):
        if uid not in upload_state: return await m.answer("❌ لطفاً از ابتدا شروع کن")
        gr, ma = t.replace("رشته:", "").split("|")
        state = upload_state[uid]
        
        if state.get("mode") == "book_upload" and state.get("step") == "book_major":
            state["grade"] = gr; state["major"] = ma; state["step"] = "book_subject"
            return await m.answer(f"📖 {state['publisher']} - {gr} - {ma}\n\nدرس مورد نظر رو انتخاب کن:", reply_markup=await book_subject_keyboard(state["publisher"], gr, ma))
        
        if state.get("step") == "book_major":
            state["grade"] = gr; state["major"] = ma; state["step"] = "book_publisher"
            return await m.answer(f"📖 {gr} - {ma}\n\nناشر مورد نظر رو انتخاب کن:", reply_markup=await book_publisher_keyboard(gr, ma))
        
        if state.get("mode") == "admin_upload":
            state["grade"] = gr; state["major"] = ma; state["step"] = "institute"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
        
        if state.get("mode") == "user_download" and state.get("category") != "book":
            state["grade"] = gr; state["major"] = ma; state["step"] = "institute"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("🏛 موسسه را انتخاب کن", reply_markup=await institute_keyboard())
    
    if uid in upload_state and upload_state[uid].get("step") == "book_publisher":
        if t == "🔙 برگشت به منو": del upload_state[uid]; return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
        state = upload_state[uid]; state["publisher"] = t; state["step"] = "book_subject_download"
        return await m.answer(f"📖 {state['publisher']} - {state['grade']} - {state['major']}\n\nدرس مورد نظر رو انتخاب کن:", reply_markup=await book_subject_keyboard(t, state["grade"], state["major"]))
    
    if uid in upload_state and upload_state[uid].get("step") == "book_subject_download":
        if t == "🔙 برگشت به منو":
            state = upload_state[uid]; state["step"] = "book_publisher"
            return await m.answer(f"📖 {state['grade']} - {state['major']}\n\nناشر مورد نظر رو انتخاب کن:", reply_markup=await book_publisher_keyboard(state["grade"], state["major"]))
        state = upload_state[uid]; state["subject"] = t; return await show_book_archives(m, state)
    
    if uid in upload_state and upload_state[uid].get("step") == "book_subject":
        if t == "🔙 برگشت به منو":
            state = upload_state[uid]; state["step"] = "book_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"رشته:{state['grade']}|ریاضی")); kb.add(KeyboardButton(f"رشته:{state['grade']}|تجربی")); kb.add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"📖 {state['publisher']} - {state['grade']}\n\nرشته را انتخاب کن:", reply_markup=kb)
        upload_state[uid]["subject"] = t; upload_state[uid]["step"] = "waiting_for_file"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ اطلاعات ثبت شد:\n📖 {upload_state[uid]['publisher']} - {upload_state[uid]['grade']} - {upload_state[uid]['major']} - {upload_state[uid]['subject']}\n\n📤 حالا فایل رو ارسال کن (PDF)\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("step") == "institute":
        state = upload_state[uid]; state["institute"] = t; state["step"] = "subject"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in subjects.get(state["major"], []):
            kb.add(KeyboardButton(s))
        kb.add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("📚 درس را انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("step") == "subject":
        state = upload_state[uid]; state["subject"] = t; state["step"] = "teacher"
        if state.get("mode") in ["admin_upload", "user_download"]:
            kb = await teacher_keyboard(state["grade"], state["major"], state["institute"], t)
            if kb: 
                kb.add(KeyboardButton("🔙 برگشت به منو"))
                return await m.answer("👨‍🏫 دبیر را انتخاب کن:", reply_markup=kb)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("❌ دبیری برای این درس پیدا نشد.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if uid in upload_state and upload_state[uid].get("step") == "teacher":
        state = upload_state[uid]; state["teacher"] = t
        if state.get("mode") == "admin_upload":
            state["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer(f"✅ دبیر {t} انتخاب شد.\n\n📤 حالا فایل رو ارسال کن (PDF یا ویدیو)\n\n⚠️ بعد از ارسال فایل، کپشن رو وارد کن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("mode") == "user_download":
            await show_archives(m, state)
            return
    
    if t == "⚡ ادامه":
        if uid in upload_state:
            state = upload_state[uid]; state["step"] = "waiting_for_file"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("📤 فایل بعدی رو بفرست.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    # ===================== دریافت کپشن جزوه/ویدیو =====================
    if uid in upload_state and upload_state[uid].get("step") == "waiting_for_caption_file":
        state = upload_state[uid]; caption = t
        if caption == "❌ لغو": del upload_state[uid]; return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
        async for db in get_db():
            db.add(Archive(category=state.get("category","pdf"), type=state["temp_file_type"], grade=state["grade"], major=state["major"], institute=state["institute"], subject=state["subject"], teacher=state.get("teacher"), file_id=state["temp_file_id"], file_name=state["temp_file_name"], caption=caption, uploaded_by=uid)); await db.commit()
        cat = "جزوه" if state.get("category") == "pdf" else "ویدیو"
        del upload_state[uid]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ {cat} با موفقیت در دیتابیس ثبت شد!\n\n📚 {state['grade']} - {state['major']} - {state['institute']} - {state['subject']}\n👨‍🏫 دبیر: {state.get('teacher','ندارد')}\n📄 {state['temp_file_name']}\n📝 کپشن: {caption}\n\n🔹 این {cat} در بخش **{'📚 جزوه' if cat == 'جزوه' else '🎥 ویدئو'}** کاربران قابل مشاهده است.\n\nبرای آپلود بعدی، روی '⚡ ادامه' بزن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb, parse_mode="Markdown")
    
    # ===================== دریافت کپشن کتاب =====================
    if uid in upload_state and upload_state[uid].get("step") == "waiting_for_caption_book":
        state = upload_state[uid]; caption = t
        if caption == "❌ لغو": del upload_state[uid]; return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
        async for db in get_db():
            db.add(Archive(category="book", type="pdf", grade=state["grade"], major=state["major"], institute=state["publisher"], subject=state["subject"], teacher=None, book_name=state.get("book_name","معمولی"), file_id=state["temp_file_id"], file_name=state["temp_file_name"], caption=caption, uploaded_by=uid)); await db.commit()
        del upload_state[uid]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ کتاب با موفقیت در دیتابیس ثبت شد!\n\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}\n📄 {state['temp_file_name']}\n📝 کپشن: {caption}\n\n🔹 این کتاب در بخش **📖 کتاب کمک آموزشی** کاربران قابل مشاهده است.\n\nبرای آپلود کتاب بعدی، روی '⚡ ادامه' بزن.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb, parse_mode="Markdown")
    
    # ===================== آپلود جلسه - دریافت فایل =====================
    if uid in upload_state and upload_state[uid].get("mode") == "session_upload" and upload_state[uid].get("step") == "waiting_for_file":
        state = upload_state[uid]
        if not m.document and not m.video:
            return await m.answer("❌ لطفاً فایل PDF یا ویدیو ارسال کن")
        
        fid = m.document.file_id if m.document else m.video.file_id
        fname = m.document.file_name if m.document else f"video_{m.message_id}.mp4"
        ftype = "pdf" if m.document else "video"
        state["temp_file_id"] = fid
        state["temp_file_name"] = fname
        state["temp_file_type"] = ftype
        state["step"] = "waiting_for_caption_session"
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        await m.answer(
            f"✅ فایل جلسه دریافت شد!\n\n"
            f"👨‍🏫 {state['teacher_name']}\n"
            f"📚 جلسه {state['session_number']}\n"
            f"📄 {fname}\n\n"
            f"📝 حالا کپشن جلسه رو وارد کن:",
            reply_markup=kb
        )
        return
    
    # ===================== دریافت کپشن جلسه =====================
    if uid in upload_state and upload_state[uid].get("mode") == "session_upload" and upload_state[uid].get("step") == "waiting_for_caption_session":
        state = upload_state[uid]
        caption = t
        if caption == "❌ لغو":
            del upload_state[uid]
            return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
        
        async for db in get_db():
            session = Session(
                teacher_id=state["teacher_id"],
                session_number=state["session_number"],
                title=caption,
                file_id=state["temp_file_id"],
                file_name=state["temp_file_name"],
                caption=caption,
                uploaded_by=uid
            )
            db.add(session)
            await db.commit()
        
        del upload_state[uid]
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        await m.answer(
            f"✅ جلسه با موفقیت در دیتابیس ثبت شد!\n\n"
            f"👨‍🏫 {state['teacher_name']}\n"
            f"📚 جلسه {state['session_number']}\n"
            f"📄 {state['temp_file_name']}\n"
            f"📝 کپشن: {caption}\n\n"
            f"برای آپلود جلسه بعدی، روی '⚡ ادامه' بزن.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return
    
    if t == "🗑 حذف دبیر":
        upload_state[uid] = {"mode": "delete_teacher", "step": "ask_institute"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("🗑 **حذف دبیر**\n\nموسسه رو انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=await institute_keyboard())
    
    if uid in upload_state and upload_state[uid].get("mode") == "delete_teacher":
        state = upload_state[uid]
        if state.get("step") == "ask_institute":
            state["institute"] = t; state["step"] = "ask_grade"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("دهم"); kb.add("یازدهم"); kb.add("دوازدهم"); kb.add("❌ لغو"); kb.add("🔙 برگشت به منو")
            return await m.answer(f"🏛 موسسه: {t}\n\nپایه رو انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_grade":
            state["grade"] = t; state["step"] = "ask_major"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("ریاضی"); kb.add("تجربی"); kb.add("انسانی"); kb.add("❌ لغو"); kb.add("🔙 برگشت به منو")
            return await m.answer(f"🏛 موسسه: {state['institute']}\n📚 پایه: {t}\n\nرشته رو انتخاب کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
        if state.get("step") == "ask_major":
            state["major"] = t
            state["step"] = "ask_teacher"
            async for db in get_db():
                pub = await db.scalar(select(Publisher).where(Publisher.name == state["institute"]))
                if not pub: return await m.answer("❌ موسسه پیدا نشد")
                teachers = (await db.execute(select(Teacher).where(Teacher.publisher_id == pub.id, Teacher.grade == state["grade"], Teacher.major == t))).scalars().all()
            if not teachers:
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
                return await m.answer("❌ دبیری برای این انتخاب‌ها پیدا نشد.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for teacher in teachers: kb.add(KeyboardButton(teacher.name))
            kb.add("❌ لغو"); kb.add("🔙 برگشت به منو")
            state["teachers_list"] = {teacher.name: teacher.id for teacher in teachers}
            return await m.answer(
                f"🏛 موسسه: {state['institute']}\n"
                f"📚 پایه: {state['grade']}\n"
                f"🎓 رشته: {state['major']}\n\n"
                "دبیر مورد نظر برای حذف رو انتخاب کن:\n\n"
                "💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.",
                reply_markup=kb
            )
        if state.get("step") == "ask_teacher":
            if t == "❌ لغو": del upload_state[uid]; return await m.answer("❌ لغو شد", reply_markup=await main_menu(uid))
            if t == "🔙 برگشت به منو": del upload_state[uid]; return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
            tid = state.get("teachers_list", {}).get(t)
            if not tid: return await m.answer("❌ دبیر پیدا نشد")
            async for db in get_db():
                teacher = await db.scalar(select(Teacher).where(Teacher.id == tid))
                if teacher: await db.delete(teacher); await db.commit()
            await m.answer(f"✅ دبیر {t} با موفقیت حذف شد!")
            del upload_state[uid]
            return await m.answer("👑 پنل مدیریت", reply_markup=admin_kb())
    
    # ===================== نمایش جلسات (کاربر) =====================
    if uid in upload_state and upload_state[uid].get("mode") == "session_select":
        session_text = t
        if session_text == "🔙 برگشت به منو":
            del upload_state[uid]
            return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
        
        if not session_text.startswith("جلسه "):
            return await m.answer("❌ لطفاً یکی از جلسات رو انتخاب کن")
        
        try:
            session_num = int(session_text.replace("جلسه ", "").strip())
        except:
            return await m.answer("❌ شماره جلسه نامعتبر")
        
        state = upload_state[uid]
        teacher_id = state.get("teacher_id")
        
        async for db in get_db():
            session = await db.scalar(
                select(Session).where(
                    Session.teacher_id == teacher_id,
                    Session.session_number == session_num
                )
            )
        
        if not session:
            return await m.answer(f"❌ جلسه {session_num} پیدا نشد")
        
        await send_file_with_timer(m.bot, uid, session.file_id, session.caption)
        del upload_state[uid]
        kb = await main_menu(uid)
        await m.answer("✅ فایل جلسه ارسال شد", reply_markup=kb)
        return
    
    if t == "👥 لیست کاربران": return await list_users(m)
    if t == "⚙️ تنظیمات":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("👤 تغییر ادمین"); kb.add("📢 پیام همگانی"); kb.add("🔙 برگشت به منو")
        return await m.answer("⚙️ **پنل تنظیمات**\n\n🔹 تغییر ادمین: آیدی جدید رو وارد کن\n🔹 پیام همگانی: به همه کاربران پیام بفرست\n\n⚠️ **توجه:** این تنظیمات فقط برای ادمین قابل دسترسه.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb, parse_mode="Markdown")
    if t == "💾 بکاپ": return await backup_database(m)
    if t == "📢 پیام همگانی":
        upload_state[uid] = {"mode": "broadcast", "step": "waiting_for_message"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ لغو").add("🔙 برگشت به منو")
        return await m.answer("📢 **ارسال پیام همگانی**\n\nپیام مورد نظر رو وارد کن:\n\n⚠️ این پیام به **همه کاربران** ارسال میشه.\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    if uid in upload_state and upload_state[uid].get("mode") == "broadcast" and upload_state[uid].get("step") == "waiting_for_message":
        if t in ["❌ لغو", "🔙 برگشت به منو"]: del upload_state[uid]; return await m.answer("🔙 به منوی اصلی برگشتی.", reply_markup=await main_menu(uid))
        await m.answer("⏳ **در حال ارسال پیام به کاربران...**")
        try:
            async for db in get_db(): users = (await db.execute(select(User))).scalars().all()
            sent, failed = 0, 0
            for user in users:
                try: await m.bot.send_message(user.telegram_id, f"📢 **پیام همگانی**\n\n{t}", parse_mode="Markdown"); sent += 1; await asyncio.sleep(0.05)
                except: failed += 1
            await m.answer(f"✅ **پیام همگانی ارسال شد!**\n\n📤 ارسال شده: {sent}\n❌ ناموفق: {failed}\n👥 کل کاربران: {len(users)}")
        except Exception as e: await m.answer(f"❌ خطا در ارسال پیام همگانی:\n`{str(e)}`", parse_mode="Markdown")
        del upload_state[uid]; return await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(uid))
    
    if t == "❌ لغو":
        if uid in upload_state: del upload_state[uid]
        return await m.answer("❌ آپلود لغو شد", reply_markup=await main_menu(uid))
    
    if uid in upload_state and upload_state[uid].get("mode") == "admin_delete": return await delete_file(m, t)
    if t == "📋 لیست فایل‌ها": return await list_files(m)
    if t == "🗑 حذف فایل":
        upload_state[uid] = {"mode": "admin_delete", "step": "waiting_for_file_id"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("🗑 آیدی فایل مورد نظر برای حذف رو وارد کن:\n\nمثلاً: `file_123456789`\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb, parse_mode="Markdown")
    if t == "📊 آمار": return await show_stats(m)

# ========================= ADMIN FUNCTIONS =========================
async def list_users(m: types.Message, page=1):
    per_page = 10
    try:
        async for db in get_db():
            total = await db.scalar(select(func.count()).select_from(User))
            offset = (page-1)*per_page
            users = (await db.execute(select(User).order_by(User.id.desc()).offset(offset).limit(per_page))).scalars().all()
        if not users: return await m.answer("❌ هیچ کاربری در دیتابیس وجود ندارد")
        text = f"👥 **لیست کاربران** (صفحه {page} از {(total+per_page-1)//per_page})\n\n📊 **تعداد کل:** {total}\n\n"
        for i,u in enumerate(users, start=offset+1):
            text += f"{i}. {u.full_name} - @{u.username if u.username else 'ندارد'}\n   🆔 {u.telegram_id}\n"
        kb = types.InlineKeyboardMarkup(row_width=2)
        if page > 1: kb.insert(types.InlineKeyboardButton("◀️ قبلی", callback_data=f"users_page_{page-1}"))
        if page*per_page < total: kb.insert(types.InlineKeyboardButton("▶️ بعدی", callback_data=f"users_page_{page+1}"))
        back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        await m.answer(text, reply_markup=back_kb, parse_mode="Markdown")
        if kb.inline_keyboard: await m.answer("📌 برای رفتن به صفحه بعد/قبل از دکمه‌های زیر استفاده کن:", reply_markup=kb)
    except Exception as e: await m.answer(f"❌ خطا در دریافت لیست کاربران:\n`{str(e)}`", parse_mode="Markdown")

async def backup_database(m: types.Message):
    await m.answer("⏳ **در حال گرفتن بکاپ از دیتابیس...**")
    try:
        async for db in get_db():
            uc = await db.scalar(select(func.count()).select_from(User))
            fc = await db.scalar(select(func.count()).select_from(Archive))
            pc = await db.scalar(select(func.count()).select_from(Publisher))
            tc = await db.scalar(select(func.count()).select_from(Teacher))
            sc = await db.scalar(select(func.count()).select_from(Session))
        await m.answer(f"📊 **گزارش بکاپ دیتابیس**\n\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n👥 کاربران: {uc}\n📄 فایل‌ها: {fc}\n🏛 انتشارات: {pc}\n👨‍🏫 دبیران: {tc}\n📚 جلسات: {sc}\n\n---\nاین یک بکاپ ساده است. برای بکاپ کامل از سیستم دیتابیس استفاده کنید.", parse_mode="Markdown")
    except Exception as e: await m.answer(f"❌ خطا در گرفتن بکاپ:\n`{str(e)}`", parse_mode="Markdown")
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def show_stats(m: types.Message):
    async for db in get_db():
        uc = await db.scalar(select(func.count()).select_from(User))
        fc = await db.scalar(select(func.count()).select_from(Archive))
        pdf = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "pdf"))
        vid = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "video"))
        bk = await db.scalar(select(func.count()).select_from(Archive).where(Archive.category == "book"))
        sc = await db.scalar(select(func.count()).select_from(Session))
    await m.answer(f"📊 **آمار ربات**\n\n👥 کاربران: {uc}\n📄 کل فایل‌ها: {fc}\n📁 جزوه: {pdf}\n🎥 ویدیو: {vid}\n📖 کتاب: {bk}\n📚 جلسات: {sc}", parse_mode="Markdown")
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def list_files(m: types.Message):
    async for db in get_db():
        files = (await db.execute(select(Archive).order_by(Archive.id.desc()).limit(20))).scalars().all()
    if not files: return await m.answer("❌ هیچ فایلی در دیتابیس وجود ندارد")
    for f in files:
        cat = {"pdf":"📄 جزوه","video":"🎥 ویدیو","book":"📖 کتاب"}.get(f.category,"📄")
        cap = f"\n📝 {f.caption}" if f.caption else ""
        await m.answer(f"{cat} **{f.file_name}**{cap}\n\n🆔 آیدی فایل: `{f.file_id[:20]}...`\n📚 پایه: {f.grade}\n🎓 رشته: {f.major}\n🏛 موسسه/ناشر: {f.institute}\n📖 درس: {f.subject}\n👨‍🏫 دبیر: {f.teacher or 'ندارد'}\n📌 کتاب: {f.book_name or 'ندارد'}", parse_mode="Markdown")
    await m.answer(f"✅ {len(files)} فایل آخر نمایش داده شد")

async def delete_file(m: types.Message, file_id: str):
    async for db in get_db():
        file = await db.scalar(select(Archive).where(Archive.file_id.like(f"%{file_id}%")))
        if file: await db.delete(file); await db.commit(); await m.answer(f"✅ فایل با موفقیت حذف شد:\n\n📄 {file.file_name}")
        else: await m.answer(f"❌ فایلی با آیدی `{file_id}` پیدا نشد")
    if m.from_user.id in upload_state: del upload_state[m.from_user.id]
    await m.answer("به منوی اصلی برگشتی", reply_markup=await main_menu(m.from_user.id))

async def show_book_archives(m: types.Message, state: dict):
    user_id = m.from_user.id
    async for db in get_db():
        archives = (await db.execute(select(Archive).where(Archive.category=="book", Archive.grade==state["grade"], Archive.major==state["major"], Archive.institute==state["publisher"], Archive.subject==state["subject"]))).scalars().all()
    if not archives:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"❌ هیچ کتابی برای این انتخاب‌ها پیدا نشد\n\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}", reply_markup=kb)
    for a in archives:
        cap = f"📖 {a.file_name}\n" + (f"📝 {a.caption}\n" if a.caption else "") + f"📌 {a.book_name or 'معمولی'}"
        await send_file_with_timer(m.bot, user_id, a.file_id, cap)
    if user_id in upload_state: del upload_state[user_id]
    await m.answer("✅ همه کتاب‌ها ارسال شد", reply_markup=await main_menu(user_id))

async def show_archives(m: types.Message, state: dict):
    user_id = m.from_user.id
    cat = state.get("category","pdf")
    
    async for db in get_db():
        # پیدا کردن دبیر
        teacher = await db.scalar(
            select(Teacher).where(
                Teacher.name == state["teacher"],
                Teacher.grade == state["grade"],
                Teacher.major == state["major"],
                Teacher.publisher_id == select(Publisher.id).where(Publisher.name == state["institute"])
            )
        )
        
        if not teacher:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
            return await m.answer("❌ دبیر پیدا نشد", reply_markup=kb)
        
        # گرفتن جلسات
        sessions = (await db.execute(
            select(Session).where(Session.teacher_id == teacher.id).order_by(Session.session_number)
        )).scalars().all()
    
    if not sessions:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer("❌ هیچ جلسه‌ای برای این دبیر پیدا نشد", reply_markup=kb)
    
    # نمایش لیست جلسات
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in sessions:
        kb.add(KeyboardButton(f"جلسه {s.session_number}"))
    kb.add(KeyboardButton("🔙 برگشت به منو"))
    
    upload_state[user_id] = {
        "mode": "session_select",
        "teacher_id": teacher.id,
        "state": state
    }
    
    await m.answer(
        f"👨‍🏫 **{state['teacher']}**\n"
        f"📚 {state['grade']} - {state['major']} - {state['subject']}\n\n"
        f"جلسه مورد نظر رو انتخاب کن:",
        reply_markup=kb
    )

# ========================= HANDLE FILE =========================
async def handle_file(m: types.Message):
    uid = m.from_user.id
    if m.chat.id == CHANNEL_ID or (m.forward_from_chat and m.forward_from_chat.id == CHANNEL_ID): return await auto_save_from_channel(m)
    if uid not in upload_state: return await m.answer("❌ ابتدا از پنل ادمین آپلود رو شروع کن")
    state = upload_state[uid]
    
    if state.get("mode") == "fast_upload":
        cap = m.caption or ""
        parts = [p.strip() for p in cap.split("|")]
        if len(parts) < 5: return await m.answer("❌ فرمت کپشن اشتباهه!\n\nمثال: `جزوه | ماز | دهم | ریاضی | فیزیک | محمدرضا شجاعی`", parse_mode="Markdown")
        cat, inst, gr, ma, sub = parts[:5]; teach = parts[5] if len(parts)>5 else None; bn = parts[6] if len(parts)>6 else None
        async for db in get_db():
            db.add(Archive(category={"جزوه":"pdf","ویدیو":"video","کتاب":"book"}.get(cat,"pdf"), type="pdf" if m.document else "video", grade=gr, major=ma, institute=inst, subject=sub, teacher=teach, book_name=bn, file_id=m.document.file_id if m.document else m.video.file_id, file_name=m.document.file_name if m.document else f"video_{m.message_id}.mp4", uploaded_by=uid)); await db.commit()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("⚡ ادامه")).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ فایل با موفقیت ثبت شد!\n📚 {inst} - {gr} - {ma} - {sub}", reply_markup=kb)
    
    if state.get("mode") == "book_upload" and state.get("step") == "waiting_for_file":
        if not m.document: return await m.answer("❌ لطفاً فایل PDF کتاب رو ارسال کن")
        state["temp_file_id"] = m.document.file_id; state["temp_file_name"] = m.document.file_name or "unknown.pdf"; state["step"] = "waiting_for_caption_book"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ فایل کتاب با موفقیت دریافت شد!\n\n📄 {state['temp_file_name']}\n📖 {state['publisher']} - {state['grade']} - {state['major']} - {state['subject']}\n\n📝 حالا کپشن کتاب رو وارد کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if state.get("mode") == "admin_upload" and state.get("step") == "waiting_for_file":
        if m.document: fid, fname, ftype = m.document.file_id, m.document.file_name or "unknown.pdf", "pdf"; cat = "جزوه"
        elif m.video: fid, fname, ftype = m.video.file_id, f"video_{m.video.file_id[:8]}.mp4", "video"; cat = "ویدیو"
        else: return await m.answer("❌ لطفاً فقط فایل PDF یا ویدیو ارسال کن")
        state["temp_file_id"] = fid; state["temp_file_name"] = fname; state["temp_file_type"] = ftype; state["step"] = "waiting_for_caption_file"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(f"✅ فایل {cat} با موفقیت دریافت شد!\n\n📄 {fname}\n\n📝 حالا کپشن فایل رو وارد کن:\n\n💡 برای برگشت، روی دکمه **🔙 برگشت به منو** کلیک کن یا **/start** رو بزن.", reply_markup=kb)
    
    if state.get("mode") == "session_upload" and state.get("step") == "waiting_for_file":
        if not m.document and not m.video:
            return await m.answer("❌ لطفاً فایل PDF یا ویدیو ارسال کن")
        fid = m.document.file_id if m.document else m.video.file_id
        fname = m.document.file_name if m.document else f"video_{m.message_id}.mp4"
        ftype = "pdf" if m.document else "video"
        state["temp_file_id"] = fid
        state["temp_file_name"] = fname
        state["temp_file_type"] = ftype
        state["step"] = "waiting_for_caption_session"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ لغو")).add(KeyboardButton("🔙 برگشت به منو"))
        return await m.answer(
            f"✅ فایل جلسه دریافت شد!\n\n"
            f"👨‍🏫 {state['teacher_name']}\n"
            f"📚 جلسه {state['session_number']}\n"
            f"📄 {fname}\n\n"
            f"📝 حالا کپشن جلسه رو وارد کن:",
            reply_markup=kb
        )
    
    return await m.answer("❌ وضعیت نامعتبر")

# ========================= HANDLE CALLBACK =========================
async def handle_callback(cb: types.CallbackQuery):
    if cb.data.startswith("users_page_"):
        page = int(cb.data.split("_")[2])
        await list_users(cb.message, page)
        await cb.answer()
