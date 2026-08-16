from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, or_, and_
from datetime import datetime, timedelta
import random
import asyncio
from database import crud
from database.models import Skip, Like, BlindDate
from utils.ai import analyze_music_taste, generate_blind_date_questions
from utils.matching import get_candidates_sorted, calculate_match_score
from keyboards.inline import premium_features_keyboard, browse_actions_keyboard, gaming_categories_keyboard, gaming_games_keyboard
from keyboards.reply import main_reply_keyboard
from utils.security import escape_markdown
from states.browse import Browse
from config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

POPULAR_SONGS = [
    ("Queen", "Bohemian Rhapsody"),
    ("John Lennon", "Imagine"),
    ("Eagles", "Hotel California"),
    ("Led Zeppelin", "Stairway to Heaven"),
    ("Nirvana", "Smells Like Teen Spirit"),
    ("Michael Jackson", "Billie Jean"),
    ("The Beatles", "Hey Jude"),
    ("The Beatles", "Yesterday"),
    ("Ed Sheeran", "Shape of You"),
    ("Mark Ronson ft. Bruno Mars", "Uptown Funk"),
    ("Luis Fonsi ft. Daddy Yankee", "Despacito"),
    ("Shakira", "Waka Waka"),
    ("Adele", "Rolling in the Deep"),
    ("Adele", "Someone Like You"),
    ("Billie Eilish", "Bad Guy"),
    ("The Weeknd", "Blinding Lights"),
    ("Dua Lipa", "Levitating"),
    ("Lil Nas X", "Montero"),
    ("The Kid LAROI", "Stay"),
    ("Justin Bieber", "Peaches"),
    ("Eminem", "Lose Yourself"),
    ("Eminem", "Stan"),
    ("Eminem", "The Real Slim Shady"),
    ("Eminem", "Without Me"),
    ("Eminem", "Rap God"),
    ("Drake", "God's Plan"),
    ("Travis Scott", "Sicko Mode"),
    ("Travis Scott", "Goosebumps"),
    ("Kanye West", "My Beautiful Dark Twisted Fantasy"),
    ("Kendrick Lamar", "To Pimp a Butterfly"),
    ("Pink Floyd", "The Dark Side of the Moon"),
    ("Pink Floyd", "Wish You Were Here"),
    ("Led Zeppelin", "Led Zeppelin IV"),
    ("Led Zeppelin", "Physical Graffiti"),
    ("Led Zeppelin", "Houses of the Holy"),
    ("AC/DC", "Back in Black"),
    ("AC/DC", "Highway to Hell"),
    ("AC/DC", "Thunderstruck"),
    ("Guns N' Roses", "Sweet Child O' Mine"),
    ("Guns N' Roses", "November Rain"),
    ("Guns N' Roses", "Welcome to the Jungle"),
    ("Metallica", "Enter Sandman"),
    ("Metallica", "Nothing Else Matters"),
    ("Metallica", "The Unforgiven"),
    ("Metallica", "One"),
    ("Metallica", "Master of Puppets"),
    ("Metallica", "Fade to Black"),
    ("Black Sabbath", "Paranoid"),
    ("Black Sabbath", "Iron Man"),
    ("Black Sabbath", "War Pigs"),
    ("Led Zeppelin", "Kashmir"),
    ("Led Zeppelin", "Whole Lotta Love"),
    ("Pink Floyd", "Comfortably Numb"),
    ("Pink Floyd", "Another Brick in the Wall"),
    ("Queen", "We Will Rock You"),
    ("Queen", "We Are the Champions"),
    ("Queen", "Don't Stop Me Now"),
    ("Queen", "Somebody to Love"),
    ("Queen", "Crazy Little Thing Called Love"),
    ("Queen", "I Want to Break Free"),
    ("Queen", "Radio Ga Ga"),
    ("Queen & David Bowie", "Under Pressure"),
    ("Michael Jackson", "Beat It"),
    ("Michael Jackson", "Thriller"),
    ("Michael Jackson", "Bad"),
    ("Michael Jackson", "Smooth Criminal"),
    ("Michael Jackson", "The Way You Make Me Feel"),
    ("Michael Jackson", "Man in the Mirror"),
    ("Michael Jackson", "Black or White"),
    ("Bob Dylan", "Like a Rolling Stone"),
    ("Bob Dylan", "Blowin' in the Wind"),
    ("Bob Dylan", "The Times They Are a-Changin'"),
    ("Eagles", "Take It Easy"),
    ("Eagles", "Desperado"),
    ("Eagles", "New Kid in Town"),
    ("Eagles", "Lyin' Eyes"),
    ("Eagles", "Tequila Sunrise"),
    ("Led Zeppelin", "Rock and Roll"),
    ("Led Zeppelin", "Black Dog"),
    ("Led Zeppelin", "Immigrant Song"),
    ("Led Zeppelin", "The Ocean"),
    ("Led Zeppelin", "Misty Mountain Hop"),
    ("Queen", "Another One Bites the Dust"),
    ("John Lennon", "Beautiful Boy"),
    ("John Lennon", "Woman"),
    ("The Beatles", "Let It Be"),
    ("The Beatles", "Something"),
    ("The Beatles", "Here Comes the Sun"),
    ("The Beatles", "Come Together"),
    ("The Beatles", "Penny Lane"),
    ("The Beatles", "Strawberry Fields Forever"),
    ("The Beatles", "Yellow Submarine"),
    ("The Beatles", "Eleanor Rigby"),
    ("Simon & Garfunkel", "The Sound of Silence"),
    ("Simon & Garfunkel", "Bridge over Troubled Water"),
    ("Simon & Garfunkel", "Mrs. Robinson"),
    ("The Mamas & the Papas", "California Dreamin'"),
    ("The Mamas & the Papas", "Monday Monday"),
    ("Sonny & Cher", "I Got You Babe"),
    ("The Beach Boys", "Good Vibrations"),
    ("The Beach Boys", "Wouldn't It Be Nice"),
    ("The Beach Boys", "God Only Knows"),
    ("The Beach Boys", "Sloop John B"),
    ("The Beach Boys", "Kokomo"),
    ("The Beach Boys", "Surfin' USA"),
    ("Marvin Gaye", "I Heard It Through the Grapevine"),
    ("Marvin Gaye", "What's Going On"),
    ("Marvin Gaye", "Sexual Healing"),
    ("Marvin Gaye", "Let's Get It On"),
    ("Marvin Gaye & Tammi Terrell", "Ain't No Mountain High Enough"),
    ("Aretha Franklin", "Respect"),
    ("Aretha Franklin", "Think"),
    ("Aretha Franklin", "Natural Woman"),
    ("Aretha Franklin", "Chain of Fools"),
    ("Dusty Springfield", "Son of a Preacher Man"),
    ("Janis Joplin", "Piece of My Heart"),
    ("Creedence Clearwater Revival", "Proud Mary"),
    ("Creedence Clearwater Revival", "Rollin' on the River"),
    ("Creedence Clearwater Revival", "Fortunate Son"),
    ("Bruce Springsteen", "Born to Run"),
    ("Bruce Springsteen", "Thunder Road"),
    ("Bruce Springsteen", "Badlands"),
    ("Bruce Springsteen", "Hungry Heart"),
    ("Bruce Springsteen", "Dancing in the Dark"),
    ("Bruce Springsteen", "The River"),
    ("Bruce Springsteen", "Born in the U.S.A."),
    ("Bruce Springsteen", "I'm on Fire"),
    ("Bruce Springsteen", "Glory Days"),
    ("Guns N' Roses", "Paradise City"),
    ("Guns N' Roses", "Knockin' on Heaven's Door"),
    ("Guns N' Roses", "Don't Cry"),
    ("Bon Jovi", "Livin' on a Prayer"),
    ("Bon Jovi", "You Give Love a Bad Name"),
    ("Bon Jovi", "It's My Life"),
    ("Bon Jovi", "Bad Medicine"),
    ("Bon Jovi", "Wanted Dead or Alive"),
    ("Bon Jovi", "Blaze of Glory"),
    ("Queen", "The Show Must Go On"),
    ("Queen", "Love of My Life"),
    ("Queen", "Killer Queen"),
    ("Queen", "Bicycle Race"),
    ("Queen", "Fat Bottomed Girls")
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
async def ai_match(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return

    # Получаем топ-5 кандидатов
    scored_candidates = await get_candidates_sorted(session, user, limit=5)
    if not scored_candidates:
        await callback.message.edit_text("Нет подходящих кандидатов для AI-подбора.")
        return

    # Сохраняем список в состоянии
    candidates_data = []
    for candidate, score in scored_candidates:
        candidates_data.append({
            "id": candidate.id,
            "score": round(score * 100)
        })
    await state.update_data(ai_candidates=candidates_data, ai_index=0)

    # Показываем первого кандидата
    await show_ai_candidate(callback.message, state, session, edit=False)
    await callback.answer()

async def show_ai_candidate(target, state: FSMContext, session: AsyncSession, edit: bool = False):
    data = await state.get_data()
    candidates = data.get("ai_candidates", [])
    index = data.get("ai_index", 0)
    if not candidates or index >= len(candidates):
        # Конец списка
        text = "Вы просмотрели всех AI-рекомендованных кандидатов."
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к премиум-функциям", callback_data="show_premium_features")]
        ])
        if edit:
            await target.edit_text(text, reply_markup=markup)
        else:
            await target.answer(text, reply_markup=markup)
        await state.clear()
        return

    candidate_id = candidates[index]["id"]
    score = candidates[index]["score"]
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        # Пропускаем невалидного
        await state.update_data(ai_index=index + 1)
        await show_ai_candidate(target, state, session, edit=edit)
        return

    # Формируем карточку
    from utils.helpers import format_user_card
    text = format_user_card(candidate, score)
    # Добавляем пояснение (если есть AI-ключ)
    if config.GIGACHAT_API_KEY:
        try:
            from utils.ai import get_match_explanation
            explanation = await get_match_explanation(user, candidate, score)
            text += f"\n\n🤖 AI-пояснение: {explanation}"
        except Exception as e:
            logger.error(f"AI explanation error: {e}")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"ai_like_{candidate_id}"),
         InlineKeyboardButton(text="⏭️ Скип", callback_data=f"ai_skip_{candidate_id}")],
        [InlineKeyboardButton(text="📋 Все кандидаты", callback_data="ai_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_premium_features")]
    ])

    if edit:
        if candidate.photo_file_id:
            await target.edit_media(
                InputMediaPhoto(media=candidate.photo_file_id, caption=text),
                reply_markup=markup
            )
        else:
            await target.edit_text(text, reply_markup=markup)
    else:
        if candidate.photo_file_id:
            await target.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
        else:
            await target.answer(text, reply_markup=markup)

@router.callback_query(F.data.startswith("ai_like_"))
async def ai_like(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    candidate_id = int(callback.data.split("_")[2])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return
    if not await crud.can_like(session, user):
        await callback.answer("Лимит лайков исчерпан", show_alert=True)
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Анкета не найдена")
        return
    like = await crud.create_like(session, user.id, candidate.id)
    await crud.increment_likes(session, user)
    if like.is_mutual:
        await callback.answer("Взаимный лайк! 💞", show_alert=True)
        # Отправка уведомлений о взаимности
        try:
            user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
            candidate_link = f"@{candidate.username}" if candidate.username else f"[профиль](tg://user?id={candidate.telegram_id})"
            await callback.bot.send_message(
                candidate.telegram_id,
                f"💞 Взаимный лайк! Вы и **{user.name or user.username}** понравились друг другу.\nНапишите ему: {user_link}",
                parse_mode="Markdown"
            )
            await callback.bot.send_message(
                user.telegram_id,
                f"💞 Взаимный лайк! Вы и **{candidate.name or candidate.username}** понравились друг другу.\nНапишите ему: {candidate_link}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mutual like notifications error: {e}")
    else:
        await callback.answer("Лайк поставлен!")
    await state.update_data(ai_index=state.get_data().get("ai_index", 0) + 1)
    await show_ai_candidate(callback.message, state, session, edit=True)

@router.callback_query(F.data.startswith("ai_skip_"))
async def ai_skip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    candidate_id = int(callback.data.split("_")[2])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        await crud.create_skip(session, user.id, candidate_id)
    await state.update_data(ai_index=state.get_data().get("ai_index", 0) + 1)
    await show_ai_candidate(callback.message, state, session, edit=True)
    await callback.answer()

@router.callback_query(F.data == "ai_list")
async def ai_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidates = data.get("ai_candidates", [])
    if not candidates:
        await callback.answer("Нет списка")
        return
    text = "📋 Список AI-рекомендованных:\n\n"
    for idx, c in enumerate(candidates):
        user_obj = await crud.get_user_by_id(session, c["id"])
        if user_obj:
            text += f"{idx+1}. {user_obj.name or 'Без имени'} — {c['score']}%\n"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К текущему кандидату", callback_data="ai_back_to_current")]
    ])
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "ai_back_to_current")
async def ai_back_to_current(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await show_ai_candidate(callback.message, state, session, edit=True)
    await callback.answer()

@router.callback_query(F.data == "ai_music_profile")
async def ai_music_profile(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return
    if not config.GIGACHAT_API_KEY:
        await callback.message.edit_text("AI-функции недоступны: отсутствует API-ключ GigaChat.", reply_markup=premium_features_keyboard())
        return
    await callback.message.edit_text("Анализируем ваш музыкальный вкус...")
    analysis = await analyze_music_taste(user)
    await callback.message.edit_text(f"🎵 Ваш музыкальный профиль:\n\n{analysis}", reply_markup=premium_features_keyboard())
    await callback.answer()

# ===================== Свидание вслепую (исправленное) =====================

@router.callback_query(F.data == "blind_date")
async def blind_date(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.is_premium:
        await callback.answer("Только для премиум!", show_alert=True)
        return

    # Проверяем активное свидание (где user1 или user2, и не оба listened)
    active = await session.execute(
        select(BlindDate).where(
            or_(
                and_(BlindDate.user1_id == user.id, BlindDate.user1_listened == False),
                and_(BlindDate.user2_id == user.id, BlindDate.user2_listened == False)
            )
        )
    )
    active = active.scalar_one_or_none()
    if active:
        await callback.answer("У вас уже есть активное свидание! Дождитесь партнёра.", show_alert=True)
        return

    # Ищем партнёра
    candidates = await crud.get_candidate_pool(session, user.id, limit=50)
    if not candidates:
        await callback.message.edit_text("Нет подходящих кандидатов для свидания вслепую.")
        return
    partner = random.choice(candidates)

    artist, song = random.choice(POPULAR_SONGS)

    # Создаём запись
    blind_date_obj = BlindDate(
        user1_id=user.id,
        user2_id=partner.id,
        song=song,
        artist=artist,
        user1_listened=False,
        user2_listened=False
    )
    session.add(blind_date_obj)
    await session.commit()
    await session.refresh(blind_date_obj)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Прослушал", callback_data=f"blind_date_listen_{blind_date_obj.id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"blind_date_cancel_{blind_date_obj.id}")]
    ])

    safe_artist = escape_markdown(artist)
    safe_song = escape_markdown(song)
    text = (f"🌹 Свидание вслепую с {escape_markdown(partner.name or 'партнёром')}!\n\n"
            f"🎵 Общий трек: **{safe_artist} — {safe_song}**\n\n"
            "Прослушайте и нажмите кнопку.\n"
            "⏳ Ожидаем партнёра... (автоотмена через 10 мин)")

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()

    # Уведомляем партнёра
    partner_text = (f"🌹 {user.name or 'Кто-то'} пригласил вас на свидание вслепую!\n\n"
                    f"🎵 Общий трек: **{safe_artist} — {safe_song}**\n\n"
                    "Прослушайте и нажмите кнопку.\n"
                    "⏳ Ожидаем партнёра... (автоотмена через 10 мин)")
    partner_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Прослушал", callback_data=f"blind_date_listen_{blind_date_obj.id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"blind_date_cancel_{blind_date_obj.id}")]
    ])
    try:
        await callback.bot.send_message(partner.telegram_id, partner_text, reply_markup=partner_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to send blind date invitation to partner: {e}")

    # Таймаут 10 минут
    asyncio.create_task(blind_date_timeout(blind_date_obj.id, callback.bot, session.bind))

async def blind_date_timeout(blind_date_id: int, bot, session_maker):
    await asyncio.sleep(600)
    async with session_maker() as session:
        blind_date = await session.get(BlindDate, blind_date_id)
        if not blind_date:
            return
        if blind_date.user1_listened and blind_date.user2_listened:
            return  # уже завершено
        user1 = await crud.get_user_by_id(session, blind_date.user1_id)
        user2 = await crud.get_user_by_id(session, blind_date.user2_id)
        await session.delete(blind_date)
        await session.commit()
        try:
            await bot.send_message(user1.telegram_id, "⏰ Свидание вслепую отменено по истечении времени (10 мин).")
        except: pass
        try:
            await bot.send_message(user2.telegram_id, "⏰ Свидание вслепую отменено по истечении времени (10 мин).")
        except: pass

@router.callback_query(F.data.startswith("blind_date_listen_"))
async def blind_date_listen(callback: CallbackQuery, session: AsyncSession):
    blind_date_id = int(callback.data.split("_")[-1])
    blind_date = await session.get(BlindDate, blind_date_id)
    if not blind_date:
        await callback.answer("Это свидание уже неактивно.", show_alert=True)
        return

    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return

    if blind_date.user1_id != user.id and blind_date.user2_id != user.id:
        await callback.answer("Вы не участник этого свидания.", show_alert=True)
        return

    # Отмечаем прослушивание
    if blind_date.user1_id == user.id:
        blind_date.user1_listened = True
    else:
        blind_date.user2_listened = True
    await session.commit()

    await callback.answer("Отлично! Ждём партнёра.")

    if blind_date.user1_listened and blind_date.user2_listened:
        # Оба прослушали – завершаем
        await callback.message.edit_reply_markup(reply_markup=None)
        user1 = await crud.get_user_by_id(session, blind_date.user1_id)
        user2 = await crud.get_user_by_id(session, blind_date.user2_id)

        def contact_link(u):
            if u.username:
                return f"@{u.username}"
            else:
                return f"[профиль](tg://user?id={u.telegram_id})"

        link1 = contact_link(user1)
        link2 = contact_link(user2)

        text1 = (f"💞 Свидание вслепую состоялось!\n"
                 f"Вы оба прослушали трек **{blind_date.artist} — {blind_date.song}**.\n"
                 f"Контакты партнёра: {link2}")
        text2 = (f"💞 Свидание вслепую состоялось!\n"
                 f"Вы оба прослушали трек **{blind_date.artist} — {blind_date.song}**.\n"
                 f"Контакты партнёра: {link1}")
        try:
            await callback.bot.send_message(user1.telegram_id, text1, parse_mode="Markdown")
        except: pass
        try:
            await callback.bot.send_message(user2.telegram_id, text2, parse_mode="Markdown")
        except: pass
        await callback.message.answer("🎉 Свидание завершено! Контакты отправлены.")
        await session.delete(blind_date)
        await session.commit()
    else:
        await callback.message.answer("✅ Вы подтвердили прослушивание. Ожидаем партнёра...")

@router.callback_query(F.data.startswith("blind_date_cancel_"))
async def blind_date_cancel(callback: CallbackQuery, session: AsyncSession):
    blind_date_id = int(callback.data.split("_")[-1])
    blind_date = await session.get(BlindDate, blind_date_id)
    if not blind_date:
        await callback.answer("Уже неактивно", show_alert=True)
        return

    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or (blind_date.user1_id != user.id and blind_date.user2_id != user.id):
        await callback.answer("Вы не участник", show_alert=True)
        return

    # Уведомляем другого участника
    other_id = blind_date.user2_id if blind_date.user1_id == user.id else blind_date.user1_id
    other = await crud.get_user_by_id(session, other_id)
    try:
        await callback.bot.send_message(other.telegram_id, "❌ Свидание вслепую отменено другим участником.")
    except: pass

    await session.delete(blind_date)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Свидание отменено.")
    await callback.answer()

# ===================== Конец свидания вслепую =====================

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