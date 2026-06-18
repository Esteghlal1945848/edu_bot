from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.core import get_db
from database.models import Content, Teacher
from utils.keyboards import Keyboards

router = Router()

class UploadStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_grade = State()
    waiting_for_lesson = State()
    waiting_for_chapter = State()
    waiting_for_teacher = State()
    waiting_for_tags = State()
    waiting_for_file = State()

def is_admin(user_id: int) -> bool:
    admin_ids = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    return user_id in admin_ids

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ دسترسی غیرمجاز!")
        return
    await message.answer("🔐 <b>پنل مدیریت</b>\n\nعملیات مورد نظر را انتخاب کنید:", 
                        reply_markup=Keyboards.admin_panel(), parse_mode="HTML")

@router.message(Command("upload"))
async def start_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ دسترسی غیرمجاز!")
        return
    await message.answer("📁 <b>آپلود فایل جدید</b>\n\nلطفاً نوع محتوا را انتخاب کنید:",
                        reply_markup=Keyboards.content_type_menu(), parse_mode="HTML")
    await state.set_state(UploadStates.waiting_for_type)

@router.callback_query(F.data.startswith("content_type:"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    content_type = callback.data.split(":")[1]
    await state.update_data(content_type=content_type)
    await callback.message.edit_text("لطفاً پایه تحصیلی را انتخاب کنید:", 
                                     reply_markup=Keyboards.grade_menu())
    await state.set_state(UploadStates.waiting_for_grade)
    await callback.answer()

@router.callback_query(F.data.startswith("grade:"))
async def process_grade(callback: CallbackQuery, state: FSMContext):
    grade = callback.data.split(":")[1]
    await state.update_data(grade=grade)
    await callback.message.edit_text("لطفاً درس را انتخاب کنید:",
                                     reply_markup=Keyboards.lesson_menu(grade))
    await state.set_state(UploadStates.waiting_for_lesson)
    await callback.answer()

@router.callback_query(F.data.startswith("lesson:"))
async def process_lesson(callback: CallbackQuery, state: FSMContext):
    lesson = callback.data.split(":")[1]
    await state.update_data(lesson=lesson)
    await callback.message.edit_text("لطفاً شماره فصل را وارد کنید (مثال: ۳) یا /skip بزنید:")
    await state.set_state(UploadStates.waiting_for_chapter)
    await callback.answer()

@router.message(UploadStates.waiting_for_chapter)
async def process_chapter(message: Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(chapter=message.text)
    await message.answer("لطفاً نام دبیر را وارد کنید:")
    await state.set_state(UploadStates.waiting_for_teacher)

@router.message(UploadStates.waiting_for_teacher)
async def process_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await message.answer("لطفاً تگ‌ها را با کاما وارد کنید (مثال: تستی, تشریحی):")
    await state.set_state(UploadStates.waiting_for_tags)

@router.message(UploadStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext):
    tags = [tag.strip() for tag in message.text.split(',')]
    await state.update_data(tags=tags)
    await message.answer("📎 حالا فایل را ارسال کنید (PDF یا ویدئو)")
    await state.set_state(UploadStates.waiting_for_file)
@router.message(UploadStates.waiting_for_file, F.document | F.video)
async def process_file(message: Message, state: FSMContext):
    data = await state.get_data()
    
    if message.document:
        file_id = message.document.file_id
        file_type = 'pdf'
    else:
        file_id = message.video.file_id
        file_type = 'video'
    
    async for db in get_db():
        teacher_name = data.get('teacher')
        result = await db.execute(select(Teacher).where(Teacher.name == teacher_name))
        teacher = result.scalar_one_or_none()
        
        if not teacher:
            teacher = Teacher(name=teacher_name)
            db.add(teacher)
            await db.flush()
        
        content = Content(
            title=f"{data.get('lesson')} - پایه {data.get('grade')} - فصل {data.get('chapter', 'نامشخص')}",
            content_type=file_type,
            file_id=file_id,
            grade=data.get('grade'),
            lesson=data.get('lesson'),
            chapter=data.get('chapter'),
            tags=data.get('tags', []),
            teacher_id=teacher.id,
            uploaded_by=message.from_user.id
        )
        
        db.add(content)
        await db.commit()
    
    await message.answer(f"✅ فایل با موفقیت آپلود شد!\n📋 شناسه: <code>{file_id}</code>", parse_mode="HTML")
    await state.clear()