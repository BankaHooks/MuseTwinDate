from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from datetime import datetime, timedelta
import random
from database import crud
from database.models import Skip, Like
from utils.ai import generate_icebreakers, analyze_music_taste, get_match_recommendation, generate_blind_date_questions
from keyboards.inline import premium_features_keyboard
from keyboards.reply import main_reply_keyboard
from utils.security import escape_markdown

router = Router()

POPULAR_SONGS = [
    "Bohemian Rhapsody", "Imagine", "Hotel California", "Stairway to Heaven",
    "Smells Like Teen Spirit", "Billie Jean", "Hey Jude", "Yesterday",
    "Shape of You", "Uptown Funk", "Despacito", "Waka Waka",
    "Rolling in the Deep", "Someone Like You", "Bad Guy", "Blinding Lights",
    "Levitating", "Montero", "Stay", "Peaches", "Lose Yourself",
    "Stan", "The Real Slim Shady", "Without Me", "Rap God", "God's Plan",
    "Sicko Mode", "Goosebumps", "My Beautiful Dark Twisted Fantasy",
    "To Pimp a Butterfly", "The Dark Side of the Moon", "Wish You Were Here",
    "Led Zeppelin IV", "Physical Graffiti", "Houses of the Holy",
    "Back in Black", "Highway to Hell", "Thunderstruck",
    "Sweet Child O' Mine", "November Rain", "Welcome to the Jungle",
    "Enter Sandman", "Nothing Else Matters", "The Unforgiven",
    "One", "Master of Puppets", "Fade to Black", "Paranoid",
    "Iron Man", "War Pigs", "Kashmir", "Whole Lotta Love",
    "Comfortably Numb", "Another Brick in the Wall", "We Will Rock You",
    "We Are the Champions", "Don't Stop Me Now", "Somebody to Love",
    "Crazy Little Thing Called Love", "I Want to Break Free", "Radio Ga Ga",
    "Under Pressure", "Beat It", "Thriller", "Bad", "Smooth Criminal",
    "The Way You Make Me Feel", "Man in the Mirror", "Black or White",
    "Like a Rolling Stone", "Blowin' in the Wind", "The Times They Are a-Changin'",
    "Take It Easy", "Desperado", "New Kid in Town", "Lyin' Eyes",
    "Tequila Sunrise", "Rock and Roll", "Black Dog", "Immigrant Song",
    "The Ocean", "Misty Mountain Hop", "Another One Bites the Dust",
    "Beautiful Boy", "Woman", "Let It Be", "Something", "Here Comes the Sun",
    "Come Together", "Penny Lane", "Strawberry Fields Forever",
    "Yellow Submarine", "Eleanor Rigby", "The Sound of Silence",
    "Bridge over Troubled Water", "Mrs. Robinson", "California Dreamin'",
    "Monday Monday", "I Got You Babe", "Good Vibrations", "Wouldn't It Be Nice",
    "God Only Knows", "Sloop John B", "Kokomo", "Surfin' USA",
    "I Heard It Through the Grapevine", "What's Going On", "Sexual Healing",
    "Let's Get It On", "Ain't No Mountain High Enough", "Respect",
    "Think", "Natural Woman", "Chain of Fools", "Son of a Preacher Man",
    "Piece of My Heart", "Proud Mary", "Rollin' on the River", "Fortunate Son",
    "Born to Run", "Thunder Road", "Badlands", "Hungry Heart",
    "Dancing in the Dark", "The River", "Born in the U.S.A.", "I'm on Fire",
    "Glory Days", "Paradise City", "Knockin' on Heaven's Door", "Don't Cry",
    "Livin' on a Prayer", "You Give Love a Bad Name", "It's My Life",
    "Bad Medicine", "Wanted Dead or Alive", "Blaze of Glory", "The Show Must Go On",
    "Love of My Life", "Killer Queen", "Bicycle Race", "Fat Bottomed Girls"
]

@router.callback_query(F.data == "show_premium_features")
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
        from keyboards.inline import browse_actions_keyboard
        markup = browse_actions_keyboard()
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
    candidates = await crud.get_candidate_pool(session, user.id, limit=50)
    if not candidates:
        await callback.message.edit_text("Нет подходящих кандидатов для свидания вслепую.")
        return
    partner = random.choice(candidates)
    user_songs = [s.strip() for s in (user.favorite_songs or "").split(",") if s.strip()]
    partner_songs = [s.strip() for s in (partner.favorite_songs or "").split(",") if s.strip()]
    common_songs = list(set(user_songs) & set(partner_songs))
    if common_songs:
        song = random.choice(common_songs)
    else:
        song = random.choice(POPULAR_SONGS)
    questions = await generate_blind_date_questions(song, user, partner)
    safe_song = escape_markdown(song)
    partner_name = escape_markdown(partner.name or "партнёром")
    # Экранируем каждый вопрос
    safe_questions = [escape_markdown(q) for q in questions]
    if partner.username:
        partner_link = f"@{partner.username}"
    else:
        partner_link = f"[профиль](tg://user?id={partner.telegram_id})"
    text = f"🌹 Свидание вслепую с {partner_name}!\n\n"
    text += f"🎵 Общий трек для прослушивания: **{safe_song}**\n\n"
    text += "Обсудите эти вопросы после прослушивания:\n"
    for i, q in enumerate(safe_questions, 1):
        text += f"{i}. {q}\n"
    text += f"\nНапишите партнёру: {partner_link}\n"
    text += "Обсудите трек и поделитесь впечатлениями!"
    await callback.message.edit_text(text, reply_markup=premium_features_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "reset_history")
async def reset_history(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    if user.last_reset and user.last_reset > datetime.utcnow() - timedelta(days=30):
        await callback.answer("Вы уже сбрасывали историю в этом месяце. Попробуйте через месяц.", show_alert=True)
        return
    await session.execute(delete(Skip).where(Skip.user_id == user.id))
    await session.execute(delete(Like).where(Like.from_user_id == user.id))
    user.likes_today = 0
    user.last_like_date = None
    user.last_reset = datetime.utcnow()
    await session.commit()
    await callback.message.edit_text("История лайков и скипов сброшена. Вы можете начать поиск заново!", reply_markup=premium_features_keyboard())
    await callback.answer()