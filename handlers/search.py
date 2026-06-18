from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, or_, and_
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.core import get_db
from database.models import Content, Teacher, SearchLog
from search.fuzzy_search import FuzzySearchEngine
from services.redis_service import RedisService

router = Router()
search_engine = FuzzySearchEngine()
redis_service = RedisService()

@router.message(F.text.contains("جزوه"))
async def search_pdf_prompt(message: Message, state: FSMContext):
    await state.update_data(content_type='pdf')
    await message.answer("📚 لطفاً عبارت مورد نظر برای جستجوی جزوه را وارد کنید (مثلاً: ریاضی نهم فصل ۳):")

@router.message(F.text.contains("ویدئو"))
async def search_video_prompt(message: Message, state: FSMContext):
    await state.update_data(content_type='video')
    await message.answer("🎥 لطفاً عبارت مورد نظر برای جستجوی ویدئو را وارد کنید:")

@router.message(F.text.contains("دبیر"))
async def search_teacher_prompt(message: Message):
    await message.answer("👨‍🏫 لطفاً نام دبیر مورد نظر را وارد کنید:")

@router.message(F.text)
async def handle_search(message: Message, state: FSMContext):
    if len(message.text) < 2:
        return
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    query = message.text.strip()
    user_data = await state.get_data()
    content_type = user_data.get('content_type')
    
    cached = await redis_service.get_cached_search(f"{query}:{content_type}")
    if cached:
        result_text = f"🔍 نتایج برای: <b>{query}</b>\n\n"
        result_text += f"📊 تعداد نتایج: {len(cached)}\n\n"
        for i, item in enumerate(cached[:5], 1):
            result_text += f"{i}. 📚 <b>{item.get('title', '')}</b>\n"
        await message.answer(result_text, parse_mode="HTML")
        return
    
    async for db in get_db():
        stmt = select(Content).where(
            or_(
                Content.title.ilike(f'%{query}%'),
                Content.description.ilike(f'%{query}%'),
                Content.tags.cast(str).ilike(f'%{query}%')
            )
        )
        if content_type:
            stmt = stmt.where(Content.content_type == content_type)
        
        result = await db.execute(stmt.limit(10))
        contents = result.scalars().all()
        
        results_list = [{
            'id': c.id,
            'title': c.title,
            'content_type': c.content_type,
            'grade': c.grade,
            'lesson': c.lesson,
            'file_id': c.file_id
        } for c in contents]
        
        await redis_service.cache_search(f"{query}:{content_type}", results_list)
        await redis_service.increment_stat('total_searches')
        
        if not results_list:
            suggestion = search_engine.suggest_correction(query)
            if suggestion:
                await message.answer(
                    f"❌ نتیجه‌ای یافت نشد!\n🤔 منظور شما \"<b>{suggestion}</b>\" بود؟",
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ نتیجه‌ای یافت نشد. لطفاً عبارت دیگری را امتحان کنید.")
            return
        
        result_text = f"🔍 نتایج برای: <b>{query}</b>\n\n📊 {len(results_list)} نتیجه یافت شد:\n\n"
        for i, item in enumerate(results_list[:5], 1):
            icon = "🎥" if item['content_type'] == 'video' else "📚"
            result_text += f"{i}. {icon} <b>{item['title']}</b>\n"
            result_text += f"   📖 {item.get('lesson', '')} - پایه {item.get('grade', '')}\n"
            result_text += "➖➖➖➖➖➖➖➖\n"
        
        await message.answer(result_text, parse_mode="HTML")