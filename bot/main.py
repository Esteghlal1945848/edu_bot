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
CHANNEL_ID = -1003918140957  # آیدی کانال خصوصی خودت رو اینجا بذار


# =========================
# دریافت خودکار فایل از کانال خصوصی
# =========================
async def auto_save_from_channel(message: types.Message):
    
    # چک کن که پیام از کانال ماست
    if message.chat.id != CHANNEL_ID:
        return
    
    # فقط اگه ادمین فرستاده باشه
    if message.from_user.id != ADMIN_ID:
        return
    
    # اگر فایل نبود، هیچ کاری نکن
    if not message.document and not message.video:
        return
    
    # گرفتن کپشن پیام
    caption = message.caption or ""
    
    # پیدا کردن هشتگ‌ها از کپشن
    tags = re.findall(r'#([^#\s]+)', caption)
    
    # حذف فاصله‌های اضافی از هشتگ‌ها
    tags = [t.strip() for t in tags]
    
    # اگر هشتگ‌ها کم بود، پیام بده
    if len(tags) < 5:
        await message.answer(
            "❌ کپشن باید حداقل ۵ هشتگ داشته باشه:\n"
            "#موسسه #پایه #رشته #درس #دبیر"
        )
        return
    
    # تبدیل هشتگ‌ها به متن بدون هشتگ برای ذخیره در دیتابیس
    institute = tags[0].replace("_", " ") if len(tags) > 0 else ""
    grade = tags[1].replace("_", " ") if len(tags) > 1 else ""
    major = tags[2].replace("_", " ") if len(tags) > 2 else ""
    subject = tags[3].replace("_", " ") if len(tags) > 3 else ""
    teacher = tags[4].replace("_", " ") if len(tags) > 4 else ""
    
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
        token=os.getenv(
            "BOT_TOKEN"
        )
    )

    storage = RedisStorage2(

        host=os.getenv(
            "REDIS_HOST",
            "redis"
        ),

        port=int(
            os.getenv(
                "REDIS_PORT",
                6379
            )
        ),

        password=os.getenv(
            "REDIS_PASSWORD",
            ""
        )
    )

    dp = Dispatcher(
        bot,
        storage=storage
    )

    # =====================
    # ثبت هندلرها
    # =====================

    # استارت
    dp.register_message_handler(
        cmd_start,
        commands=["start"]
    )

    # دکمه‌ها
    dp.register_message_handler(
        handle_buttons
    )

    # آپلود فایل توسط ادمین (از طریق پنل)
    dp.register_message_handler(
        handle_file,
        content_types=['document', 'video']
    )

    # دریافت خودکار از کانال خصوصی
    dp.register_message_handler(
        auto_save_from_channel,
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
