from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from utils.ai import generate_icebreakers, analyze_music_taste, get_match_recommendation, generate_blind_date_questions
from keyboards.inline import premium_features_keyboard, browse_actions_keyboard
from keyboards.reply import main_reply_keyboard
import random

router = Router()

@router.callback_query(F.data == "premium_features")
async def premium_features_menu(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    if not user.is_premium:
        await callback.answer("Эта функция доступна только с премиум-подпиской!", show_alert=True)
        return
    await callback.message.edit_text("Доступные премиум-функции:", reply_markup=premium_features_keyboard())
    await callback.answer()

@router.callback_query(F.data == "ai_match")
async def ai_match(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    await callback.message.edit_text("Ищу идеальную пару с помощью AI...")
    pool = await crud.get_candidate_pool(session, user.id)
    if not pool:
        await callback.message.edit_text("Нет кандидатов для подбора.")
        return
    result = await get_match_recommendation(user, pool)
    if result["user"]:
        candidate = result["user"]
        text = f"🎯 AI рекомендует:\n\nИмя: {candidate.name or 'Без имени'}\n"
        if candidate.age:
            text += f"Возраст: {candidate.age}\n"
        if candidate.city:
            text += f"Город: {candidate.city}\n"
        text += f"\nПричина: {result['explanation']}\n\n"
        text += "Хотите посмотреть анкету этого человека?"
        markup = browse_actions_keyboard()  # можно использовать существующую клавиатуру
        await callback.message.edit_text(text, reply_markup=markup)
    else:
        await callback.message.edit_text(result["explanation"])
    await callback.answer()

@router.callback_query(F.data == "ai_music_profile")
async def ai_music_profile(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    await callback.message.edit_text("Анализируем ваш музыкальный вкус...")
    analysis = await analyze_music_taste(user)
    await callback.message.edit_text(f"🎵 Ваш музыкальный профиль:\n\n{analysis}", reply_markup=premium_features_keyboard())
    await callback.answer()

@router.callback_query(F.data == "blind_date")
async def blind_date(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    # Подбираем случайного кандидата, который не был лайкнут и не скипнут
    candidates = await crud.get_candidate_pool(session, user.id, limit=50)
    if not candidates:
        await callback.message.edit_text("Нет подходящих кандидатов для свидания вслепую.")
        return
    partner = random.choice(candidates)
    # Выбираем общую песню (например, первую из списка песен пользователя)
    user_songs = [s.strip() for s in (user.favorite_songs or "").split(",") if s.strip()]
    partner_songs = [s.strip() for s in (partner.favorite_songs or "").split(",") if s.strip()]
    common_songs = list(set(user_songs) & set(partner_songs))
    if common_songs:
        song = random.choice(common_songs)
    else:
        # Или случайная из песен пользователя
        song = random.choice(user_songs) if user_songs else "Bohemian Rhapsody"
    questions = await generate_blind_date_questions(song, user, partner)
    text = f"🌹 Свидание вслепую с {partner.name or 'партнёром'}!\n\n"
    text += f"🎵 Общий трек для прослушивания: {song}\n\n"
    text += "Обсудите эти вопросы после прослушивания:\n"
    for i, q in enumerate(questions, 1):
        text += f"{i}. {q}\n"
    text += "\nНапишите партнёру в личные сообщения, чтобы обсудить трек!"
    await callback.message.edit_text(text, reply_markup=premium_features_keyboard())
    await callback.answer()

@router.callback_query(F.data == "reset_history")
async def reset_history(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    # Проверка, не сбрасывал ли уже в этом месяце
    from datetime import datetime, timedelta
    if user.last_reset and user.last_reset > datetime.utcnow() - timedelta(days=30):
        await callback.answer("Вы уже сбрасывали историю в этом месяце. Попробуйте через месяц.", show_alert=True)
        return
    # Удаляем все скипы и лайки пользователя (как отправитель, так и получатель)
    from sqlalchemy import delete
    from database.models import Skip, Like
    await session.execute(delete(Skip).where(Skip.user_id == user.id))
    await session.execute(delete(Like).where(Like.from_user_id == user.id))
    # Обнуляем счётчики
    user.likes_today = 0
    user.last_like_date = None
    user.last_reset = datetime.utcnow()
    await session.commit()
    await callback.message.edit_text("История лайков и скипов сброшена. Вы можете начать поиск заново!", reply_markup=premium_features_keyboard())
    await callback.answer()