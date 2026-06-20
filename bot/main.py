import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import (
    RedisStorage2
)

from database.core import get_db, init_db
from database.models import Archive

from handlers.start import (
    cmd_start,
    handle_buttons,
    handle_file
)


ADMIN_ID = 7336595194
CHANNEL_ID = -1003918140957  # آیدی کانال خصوصی


# =========================
# دریافت فایل از کانال (مستقیم یا فورواردی)
# =========================
async def auto_save_from_channel(message: types.Message):
    
    # چک کن پیام از کانال اومده یا فوروارد شده از کانال
    is_from_channel = False
    chat_id = None
    
    # حالت ۱: پیام مستقیم از کانال
    if message.chat.id == CHANNEL_ID:
        is_from_channel = True
        chat_id = message.chat.id
    
    # حالت ۲: پیام فوروارد شده از کانال
    elif message.forward_from_chat and message.forward_from_chat.id == CHANNEL_ID:
        is_from_channel = True
        chat_id = message.forward_from_chat.id
    
    # اگه از کانال نبود، رد کن
    if not is_from_channel:
        return
    
    # فقط اگه ادمین فرستاده باشه
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ فقط ادمین میتونه فایل فوروارد کنه")
        return
    
    # اگر فایل نبود، هیچ کاری نکن
    if not message.document and not message.video:
        await message.answer("❌ لطفاً فایل رو فوروارد کن")
        return
    
    # گرفتن کپشن پیام (همون کپشنی که توی کانال ویرایش کردی)
    caption = message.caption or ""
    
    # پیدا کردن هشتگ‌ها از کپشن
    tags = re.findall(r'#([^#\s]+)', caption)
    
    # حذف فاصله‌های اضافی
    tags = [t.strip() for t in tags]
    
    # اگه هشتگ کم بود، راهنمایی کن
    if len(tags) < 5:
        await message.answer(
            "❌ کپشن باید ۵ هشتگ داشته باشه:\n"
            "#موسسه #پایه #رشته #درس #دبیر\n\n"
            "مثال: #تایتان #دهم #ریاضی #شیمی #فراهانی"
        )
        return
    
    # تبدیل هشتگ به متن معمولی
    institute = tags[0].replace("_", " ")
    grade = tags[1].replace("_", " ")
    major = tags[2].replace("_", " ")
    subject = tags[3].replace("_", " ")
    teacher = tags[4].replace("_", " ")
    
    # ذخیره در دیتابیس
    async for db in get_db():
        
        archive = Archive(
            type="pdf" if message.document else "video",
            grade=grade,
            major=major,
            institute=institute,
            subject=subject,
            teacher=teacher,
            file_id=message.document.file_id if message.document else message.video.file_id,
            file_name=message.document.file_name if message.document else f"video_{message.message_id}.mp4",
            uploaded_by=message.from_user.id
        )
        
        db.add(archive)
        await db.commit()
    
    # پیام موفقیت
    await message.answer(
        f"✅ فایل با موفقیت ذخیره شد!\n"
        f"📚 {institute} - {grade} - {major} - {subject} - {teacher}"
    )


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

    bot = Bot(
        token=os.getenv("BOT_TOKEN")
    )

    storage = RedisStorage2(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", "")
    )

    dp = Dispatcher(bot, storage=storage)

    # =====================
    # ثبت هندلرها
    # =====================

    # اول: دریافت از کانال (مستقیم یا فورواردی)
    dp.register_message_handler(
        auto_save_from_channel,
        content_types=['document', 'video']
    )

    # دوم: استارت
    dp.register_message_handler(
        cmd_start,
        commands=["start"]
    )

    # سوم: دکمه‌ها
    dp.register_message_handler(
        handle_buttons
    )

    # چهارم: آپلود دستی
    dp.register_message_handler(
        handle_file,
        content_types=['document', 'video']
    )

    await on_startup(dp)

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    asyncio.run(main())
