import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from database.core import get_db, init_db
from database.models import Archive

from handlers.start import cmd_start, handle_buttons, handle_file
from handlers.state import upload_state
from aiogram.types import KeyboardButton


ADMIN_ID = 7336595194
CHANNEL_ID = -1003918140957  # آیدی کانالت اینجا


# =========================
# دریافت فایل (مستقیم یا فورواردی)
# =========================
async def auto_save_from_channel(message: types.Message):

    # ========== بخش ۱: تشخیص اینکه پیام از کانال اومده یا نه ==========
    is_from_channel = False

    # حالت ۱: پیام مستقیم در کانال
    if message.chat.id == CHANNEL_ID:
        is_from_channel = True

    # حالت ۲: پیام فوروارد شده از کانال
    if message.forward_from_chat and message.forward_from_chat.id == CHANNEL_ID:
        is_from_channel = True

    # اگه هیچکدوم نبود، بیخیال
    if not is_from_channel:
        return

    # ========== بخش ۲: فقط ادمین اجازه داره ==========
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ فقط ادمین میتونه فایل فوروارد کنه")
        return

    # ========== بخش ۳: چک کن فایل هست یا نه ==========
    if not message.document and not message.video:
        await message.reply("❌ لطفاً یک فایل (PDF یا ویدیو) فوروارد کن")
        return

    # ========== بخش ۴: خوندن هشتگ‌ها از کپشن ==========
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

    # ========== بخش ۵: تبدیل هشتگ به متن ==========
    institute = tags[0].replace("_", " ")
    grade = tags[1].replace("_", " ")
    major = tags[2].replace("_", " ")
    subject = tags[3].replace("_", " ")
    teacher = tags[4].replace("_", " ")

    # استانداردسازی نام درس‌ها
    subject_map = {
        "زیست": "زیست شناسی",
        "علوم و فنون": "علوم و فنون ادبی",
        "روانشناسی": "روان شناسی",
        "دینی": "دین و زندگی",
        "ادبیات": "فارسی",
    }
    subject = subject_map.get(subject, subject)

    # ========== بخش ۶: ذخیره در دیتابیس ==========
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

    # ========== بخش ۷: پیام موفقیت ==========
    await message.reply(
        f"✅ فایل با موفقیت ذخیره شد!\n"
        f"📚 {institute} - {grade} - {major} - {subject} - {teacher}"
    )


# =========================
# هندلر کپشن (Callback)
# =========================
async def handle_caption_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if callback_query.data.startswith("caption_file_"):
        await callback_query.message.answer(
            "📝 **لطفاً کپشن فایل رو به صورت متن وارد کن:**\n\n"
            "مثال:\n"
            "شیمی دهم ریاضی تایتان - جلسه ۱\n\n"
            "⚠️ این کپشن به همراه فایل برای کاربر نمایش داده میشه.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                KeyboardButton("❌ لغو")
            )
        )
        await callback_query.answer()
        
    elif callback_query.data.startswith("caption_book_"):
        await callback_query.message.answer(
            "📝 **لطفاً کپشن کتاب رو به صورت متن وارد کن:**\n\n"
            "مثال:\n"
            "کتاب ریاضی دهم خیلی سبز - فصل ۱\n\n"
            "⚠️ این کپشن به همراه فایل برای کاربر نمایش داده میشه.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                KeyboardButton("❌ لغو")
            )
        )
        await callback_query.answer()


# =========================
# STARTUP
# =========================
async def on_startup(dp):
    await init_db()
    print("🤖 Bot started")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Channel ID: {CHANNEL_ID}")


# =========================
# MAIN
# =========================
async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
    )
    dp = Dispatcher(bot, storage=storage)

    # =====================
    # ثبت هندلرها (با اولویت درست)
    # =====================

    # 1️⃣ دریافت خودکار از کانال (فایل‌ها)
    dp.register_message_handler(
        auto_save_from_channel,
        content_types=[types.ContentType.DOCUMENT, types.ContentType.VIDEO]
    )

    # 2️⃣ استارت
    dp.register_message_handler(cmd_start, commands=["start"])

    # 3️⃣ آپلود فایل توسط ادمین (از طریق پنل)
    dp.register_message_handler(
        handle_file,
        content_types=[types.ContentType.DOCUMENT, types.ContentType.VIDEO]
    )

    # 4️⃣ دکمه‌ها و پیام‌های متنی - فقط متن
    dp.register_message_handler(
        handle_buttons,
        content_types=[types.ContentType.TEXT]
    )

    # 5️⃣ هندلر کپشن (Callback)
    dp.register_callback_query_handler(handle_caption_callback)

    # 6️⃣ هندلر عمومی برای دیباگ (هر چیزی که به دست نیومد رو بگیر)
    @dp.message_handler()
    async def catch_all(message: types.Message):
        print(f"🔍 پیام دریافت شد: {message.content_type} | متن: {message.text} | فایل: {message.document}")

    await on_startup(dp)

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
