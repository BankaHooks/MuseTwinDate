from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from datetime import datetime, timedelta
import random
import asyncio
from database import crud
from database.models import Skip, Like, BlindDate
from utils.ai import generate_icebreakers, analyze_music_taste, get_match_recommendation, generate_blind_date_questions
from keyboards.inline import premium_features_keyboard, browse_actions_keyboard
from keyboards.reply import main_reply_keyboard
from utils.security import escape_markdown
from states.browse import Browse
from config import config

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

async def cancel_blind_date_after_timeout(blind_date_id: int, bot, session_maker):
    await asyncio.sleep(600)
    async with session_maker() as session:
        blind_date = await crud.get_blind_date_by_id(session, blind_date_id)
        if not blind_date:
            return
        if blind_date.user1_listened and blind_date.user2_listened:
            return
        user1 = await crud.get_user_by_id(session, blind_date.user1_id)
        user2 = await crud.get_user_by_id(session, blind_date.user2_id)
        await session.delete(blind_date)
        await session.commit()
        try:
            await bot.send_message(user1.telegram_id, "⏰ Свидание вслепую отменено по истечении времени (10 минут). Попробуйте снова позже.")
        except:
            pass
        try:
            await bot.send_message(user2.telegram_id, "⏰ Свидание вслепую отменено по истечении времени (10 минут). Попробуйте снова позже.")
        except:
            pass

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
    if not config.GIGACHAT_API_KEY:
        await callback.message.edit_text("AI-функции недоступны: отсутствует API-ключ GigaChat.")
        return
    await callback.message.edit_text("Ищу идеальную пару с помощью AI...")
    pool = await crud.get_candidate_pool(session, user.id)
    if not pool:
        await callback.message.edit_text("Нет кандидатов для подбора.")
        return
    try:
        result = await get_match_recommendation(user, pool)
    except Exception as e:
        await callback.message.edit_text(f"Ошибка AI: {e}. Попробуйте позже.")
        return
    if result["user"]:
        candidate = result["user"]
        text = f"🎯 AI рекомендует:\n\nИмя: {candidate.name or 'Без имени'}\n"
        if candidate.age:
            text += f"Возраст: {candidate.age}\n"
        if candidate.city:
            text += f"Город: {candidate.city}\n"
        text += f"\nПричина: {result['explanation']}\n\n"
        text += "Хотите лайкнуть или пропустить?"
        await state.set_state(Browse.candidate_id)
        await state.update_data(candidate_id=candidate.id)
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
    if not config.GIGACHAT_API_KEY:
        await callback.message.edit_text("AI-функции недоступны: отсутствует API-ключ GigaChat.", reply_markup=premium_features_keyboard())
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

    active = await crud.get_active_blind_date(session, user.id)
    if active:
        await callback.answer("У вас уже есть активное свидание вслепую! Дождитесь партнёра.", show_alert=True)
        return

    candidates = await crud.get_candidate_pool(session, user.id, limit=50)
    if not candidates:
        await callback.message.edit_text("Нет подходящих кандидатов для свидания вслепую.")
        return
    partner = random.choice(candidates)

    artist, song = random.choice(POPULAR_SONGS)

    blind_date_obj = await crud.create_blind_date(session, user.id, partner.id, song, artist)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Прослушал", callback_data=f"blind_date_listen_{blind_date_obj.id}")],
        [InlineKeyboardButton(text="❌ Отменить свидание", callback_data=f"blind_date_cancel_{blind_date_obj.id}")]
    ])

    safe_artist = escape_markdown(artist)
    safe_song = escape_markdown(song)
    text = (f"🌹 Свидание вслепую с {escape_markdown(partner.name or 'партнёром')}!\n\n"
            f"🎵 Общий трек для прослушивания: **{safe_artist} — {safe_song}**\n\n"
            "Прослушайте данную музыку и затем обсудите с партнёром.\n"
            "Когда прослушаете, нажмите кнопку ниже.\n\n"
            "⏳ Ожидаем, пока партнёр тоже прослушает...\n"
            "⏱️ Свидание будет автоматически отменено через 10 минут, если второй участник не прослушает трек.")

    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        await callback.message.edit_text(
            f"🌹 Свидание вслепую с {partner.name or 'партнёром'}!\n\n"
            f"🎵 Общий трек: {artist} — {song}\n\n"
            "Прослушайте данную музыку и затем обсудите с партнёром.\n"
            "Когда прослушаете, нажмите кнопку ниже.\n\n"
            "⏳ Ожидаем, пока партнёр тоже прослушает...\n"
            "⏱️ Свидание будет автоматически отменено через 10 минут, если второй участник не прослушает трек.",
            reply_markup=markup
        )
    await callback.answer()

    partner_text = (f"🌹 Пользователь {user.name or 'кто-то'} пригласил вас на свидание вслепую!\n\n"
                    f"🎵 Общий трек для прослушивания: **{safe_artist} — {safe_song}**\n\n"
                    "Прослушайте и нажмите кнопку ниже, чтобы подтвердить.\n\n"
                    "⏳ Ожидаем, пока партнёр тоже прослушает...\n"
                    "⏱️ Свидание будет автоматически отменено через 10 минут, если вы не подтвердите прослушивание.")
    partner_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Прослушал", callback_data=f"blind_date_listen_{blind_date_obj.id}")],
        [InlineKeyboardButton(text="❌ Отменить свидание", callback_data=f"blind_date_cancel_{blind_date_obj.id}")]
    ])
    try:
        await callback.bot.send_message(partner.telegram_id, partner_text, reply_markup=partner_markup, parse_mode="Markdown")
    except Exception:
        await callback.bot.send_message(partner.telegram_id,
                                        f"🌹 Пользователь {user.name or 'кто-то'} пригласил вас на свидание вслепую!\n\n"
                                        f"🎵 Общий трек: {artist} — {song}\n\n"
                                        "Прослушайте и нажмите кнопку ниже.\n\n"
                                        "⏳ Ожидаем, пока партнёр тоже прослушает...\n"
                                        "⏱️ Свидание будет автоматически отменено через 10 минут, если вы не подтвердите прослушивание.",
                                        reply_markup=partner_markup)

    asyncio.create_task(cancel_blind_date_after_timeout(blind_date_obj.id, callback.bot, session.bind))

@router.callback_query(F.data.startswith("blind_date_listen_"))
async def blind_date_listen(callback: CallbackQuery, session: AsyncSession):
    try:
        blind_date_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный идентификатор.", show_alert=True)
        return

    blind_date = await crud.get_blind_date_by_id(session, blind_date_id)
    if not blind_date:
        await callback.answer("Это свидание уже неактивно.", show_alert=True)
        return

    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    if blind_date.user1_id != user.id and blind_date.user2_id != user.id:
        await callback.answer("Вы не участник этого свидания.", show_alert=True)
        return

    both_listened = await crud.mark_blind_date_listened(session, blind_date_id, user.id)
    await callback.answer("Отлично! Ждём партнёра.")

    if both_listened:
        await callback.message.edit_reply_markup(reply_markup=None)

        user1 = await crud.get_user_by_id(session, blind_date.user1_id)
        user2 = await crud.get_user_by_id(session, blind_date.user2_id)

        def get_contact_link(u):
            if u.username:
                return f"@{u.username}"
            else:
                return f"[профиль](tg://user?id={u.telegram_id})"

        link1 = get_contact_link(user1)
        link2 = get_contact_link(user2)

        safe_name1 = escape_markdown(user1.name or "Пользователь")
        safe_name2 = escape_markdown(user2.name or "Пользователь")

        text1 = (f"💞 Свидание вслепую состоялось!\n\n"
                 f"Вы оба прослушали трек **{blind_date.artist} — {blind_date.song}**.\n\n"
                 f"Теперь вы можете обсудить его с {safe_name2}.\n"
                 f"Контакты партнёра: {link2}\n\n"
                 "Приятного общения!")
        text2 = (f"💞 Свидание вслепую состоялось!\n\n"
                 f"Вы оба прослушали трек **{blind_date.artist} — {blind_date.song}**.\n\n"
                 f"Теперь вы можете обсудить его с {safe_name1}.\n"
                 f"Контакты партнёра: {link1}\n\n"
                 "Приятного общения!")

        try:
            await callback.bot.send_message(user1.telegram_id, text1, parse_mode="Markdown")
        except Exception:
            await callback.bot.send_message(user1.telegram_id, text1)

        try:
            await callback.bot.send_message(user2.telegram_id, text2, parse_mode="Markdown")
        except Exception:
            await callback.bot.send_message(user2.telegram_id, text2)

        await callback.message.answer("🎉 Свидание вслепую завершено! Контакты отправлены.")
    else:
        await callback.message.answer("✅ Вы подтвердили прослушивание. Ожидаем партнёра...")

@router.callback_query(F.data.startswith("blind_date_cancel_"))
async def blind_date_cancel(callback: CallbackQuery, session: AsyncSession):
    try:
        blind_date_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный идентификатор.", show_alert=True)
        return

    blind_date = await crud.get_blind_date_by_id(session, blind_date_id)
    if not blind_date:
        await callback.answer("Это свидание уже неактивно.", show_alert=True)
        return

    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    if blind_date.user1_id != user.id and blind_date.user2_id != user.id:
        await callback.answer("Вы не участник этого свидания.", show_alert=True)
        return

    user1 = await crud.get_user_by_id(session, blind_date.user1_id)
    user2 = await crud.get_user_by_id(session, blind_date.user2_id)

    await session.delete(blind_date)
    await session.commit()

    try:
        await callback.bot.send_message(user1.telegram_id, "❌ Свидание вслепую отменено другим участником.")
    except:
        pass
    try:
        await callback.bot.send_message(user2.telegram_id, "❌ Свидание вслепую отменено другим участником.")
    except:
        pass

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Свидание отменено.")
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