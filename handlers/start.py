async def handle_buttons(message: types.Message):

    text = message.text


    # کاربر

    if text == "📚 جزوه":

        await message.answer(
            "کدوم پایه‌ای؟",
            reply_markup=grade_keyboard()
        )


    elif text == "🎥 ویدئو":

        await message.answer(
            "کدوم پایه‌ای؟",
            reply_markup=grade_keyboard()
        )


    elif text in ["دهم", "یازدهم", "دوازدهم"]:

        await message.answer(
            "رشته رو انتخاب کن 👇",
            reply_markup=major_keyboard(text)
        )


    elif text.startswith("رشته:"):

        data = text.replace("رشته:", "")

        grade, major = data.split("|")

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )


    # پنل ادمین

    elif text == "👑 پنل ادمین":

        if message.from_user.id != ADMIN_ID:
            return

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add("📤 آپلود جزوه")
        keyboard.add("🎥 آپلود ویدئو")

        await message.answer(
            "👑 پنل مدیریت",
            reply_markup=keyboard
        )


    elif text == "📤 آپلود جزوه":

        if message.from_user.id != ADMIN_ID:
            return

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add("آپلود جزوه | دهم")
        keyboard.add("آپلود جزوه | یازدهم")
        keyboard.add("آپلود جزوه | دوازدهم")

        await message.answer(
            "جزوه برای کدوم پایه است؟",
            reply_markup=keyboard
        )


    elif text == "🎥 آپلود ویدئو":

        if message.from_user.id != ADMIN_ID:
            return

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add("آپلود ویدئو | دهم")
        keyboard.add("آپلود ویدئو | یازدهم")
        keyboard.add("آپلود ویدئو | دوازدهم")

        await message.answer(
            "ویدئو برای کدوم پایه است؟",
            reply_markup=keyboard
        )


    elif text.startswith("آپلود جزوه |") or text.startswith("آپلود ویدئو |"):

        if message.from_user.id != ADMIN_ID:
            return

        grade = text.split("|")[1].strip()

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(f"{grade}|ریاضی")
        keyboard.add(f"{grade}|تجربی")
        keyboard.add(f"{grade}|انسانی")

        await message.answer(
            "رشته رو انتخاب کن 👇",
            reply_markup=keyboard
        )


    elif "|" in text:

        if message.from_user.id != ADMIN_ID:
            return

        grade, major = text.split("|")

        upload_state[message.from_user.id] = {
            "grade": grade,
            "major": major
        }

        await message.answer(
            "درس رو انتخاب کن 👇",
            reply_markup=subject_keyboard(
                grade,
                major
            )
        )


    elif text in [
        "فیزیک","شیمی","ریاضی","هندسه",
        "ادبیات","عربی","زیست","منطق",
        "اقتصاد","تاریخ","ریاضی و آمار",
        "فارسی","حسابان","آمار و احتمال",
        "جغرافیا","جامعه شناسی","روان شناسی",
        "فلسفه","گسسته"
    ]:

        if message.from_user.id != ADMIN_ID:
            return

        upload_state[message.from_user.id]["subject"] = text

        await message.answer(
            "فایل را ارسال کن 📎\n\nجزوه → PDF\nویدئو → MP4"
        )
