from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from keyboards.inline import (
    welcome_keyboard, main_menu_keyboard, gender_choose_keyboard,
    genre_category_keyboard, genre_items_keyboard,
    goal_keyboard, interest_category_keyboard,
    interest_items_keyboard, games_category_keyboard, games_items_keyboard
)
from keyboards.reply import main_reply_keyboard
from states.registration import RegistrationState
from states.profile_edit import ProfileEditState
from utils.helpers import validate_age, normalize_city, validate_text_length
from utils.security import escape_markdown
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    args = message.text.split()
    ref_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1]

    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы. Используйте меню.", reply_markup=main_reply_keyboard())
        await state.clear()
        return

    await message.answer(
            "🎉 MuseTwin только что вышел!\n\n"
            "Я буду очень благодарен за помощь в развитии — "
            "зовите друзей, делитесь ссылкой, рассказывайте о боте. "
            "За активность — приятные бонусы (скидки, премиум и т.п.).\n\n"
            "Только без спама, пожалуйста 🙂"
        )

    await state.update_data(ref_code=ref_code)
    await state.set_state(RegistrationState.name)
    await message.answer("Добро пожаловать в MuseTwin – знакомства по музыке!\n\nДавайте познакомимся. Как вас зовут?")

@router.message(RegistrationState.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Имя не может быть пустым. Напишите, как вас зовут.")
        return
    if len(name) > 100:
        await message.answer("Имя слишком длинное (максимум 100 символов).")
        return
    await state.update_data(name=name)
    await state.set_state(RegistrationState.gender)
    await message.answer("Выберите ваш пол:", reply_markup=gender_choose_keyboard())

@router.callback_query(F.data.startswith("gender_"), RegistrationState.gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(RegistrationState.age)
    await callback.message.delete()
    await callback.message.answer("Сколько вам лет? (от 16 до 99)")
    await callback.answer()

@router.message(RegistrationState.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число.")
        return
    age = int(message.text)
    if not validate_age(age):
        await message.answer("Возраст должен быть от 16 до 99 лет.")
        return
    await state.update_data(age=age)
    await state.set_state(RegistrationState.city)
    await message.answer("Введите ваш город:")

@router.message(RegistrationState.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        await message.answer("Город не может быть пустым.")
        return
    city = normalize_city(city)
    await state.update_data(city=city)
    await state.set_state(RegistrationState.genres)
    await message.answer("Выберите ваши любимые музыкальные жанры (можно несколько, нажимайте на них, затем кнопка «Готово»):", reply_markup=genre_category_keyboard())

@router.callback_query(F.data.startswith("genre_cat_"), RegistrationState.genres)
async def genre_category_selected(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("genre_cat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    await state.update_data(current_genre_category=category)
    markup = genre_items_keyboard(category, selected)
    await callback.message.edit_text(f"Выберите жанры в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("genre_item_"), RegistrationState.genres)
async def genre_item_selected(callback: CallbackQuery, state: FSMContext):
    genre = callback.data[len("genre_item_"):]
    genre = genre.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if genre in selected:
        selected.remove(genre)
        await callback.answer(f"Удалено: {genre}")
    else:
        if len(selected) >= 15:
            await callback.answer("Максимум 15 жанров.", show_alert=True)
            return
        selected.append(genre)
        await callback.answer(f"Добавлено: {genre}")
    await state.update_data(selected_genres=selected)
    category = data.get("current_genre_category", "")
    if category:
        markup = genre_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "genre_back", RegistrationState.genres)
async def genre_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категорию жанров:", reply_markup=genre_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "genres_done", RegistrationState.genres)
async def genres_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if not selected:
        await callback.answer("Выберите хотя бы один жанр!", show_alert=True)
        return
    await state.update_data(genres=", ".join(selected))
    await state.set_state(RegistrationState.bands)
    await callback.message.delete()
    await callback.message.answer("Напишите ваши любимые музыкальные группы (до 5, через запятую):")
    await callback.answer()

@router.message(RegistrationState.bands)
async def process_bands(message: Message, state: FSMContext):
    bands = message.text.strip()
    if bands:
        band_list = [b.strip() for b in bands.split(",") if b.strip()]
        if len(band_list) > 5:
            await message.answer("Не более 5 групп. Напишите снова.")
            return
        await state.update_data(bands=", ".join(band_list[:5]))
    else:
        await state.update_data(bands="")
    await state.set_state(RegistrationState.songs)
    await message.answer("Напишите ваши любимые песни (до 500 символов):")

@router.message(RegistrationState.songs)
async def process_songs(message: Message, state: FSMContext):
    songs = message.text.strip()
    if songs and len(songs) > 500:
        await message.answer("Слишком длинный текст (максимум 500 символов).")
        return
    await state.update_data(songs=songs)
    await state.set_state(RegistrationState.goal)
    await message.answer("Выберите цель знакомства:", reply_markup=goal_keyboard())

@router.callback_query(F.data.startswith("goal_"), RegistrationState.goal)
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split("_")[1]
    goal_map = {
        "flirt": "Флирт",
        "communication": "Общение",
        "friendship": "Дружба",
        "relationship": "Отношения"
    }
    await state.update_data(goal=goal_map.get(goal, goal))
    await state.set_state(RegistrationState.interests)
    await callback.message.delete()
    await callback.message.answer("Выберите категории интересов:", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"), RegistrationState.interests)
async def process_interest_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("cat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    await state.update_data(current_category=category)
    markup = interest_items_keyboard(category, selected)
    await callback.message.edit_text(f"Выберите интересы в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("interest_"), RegistrationState.interests)
async def process_interest_item(callback: CallbackQuery, state: FSMContext):
    item = callback.data[len("interest_"):]
    item = item.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    if item in selected:
        selected.remove(item)
        await callback.answer(f"Удалено: {item}")
    else:
        if len(selected) >= 10:
            await callback.answer("Максимум 10 интересов.", show_alert=True)
            return
        selected.append(item)
        await callback.answer(f"Добавлено: {item}")
    await state.update_data(selected_interests=selected)
    category = data.get("current_category", "")
    if category:
        markup = interest_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "interests_back", RegistrationState.interests)
async def interests_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категории интересов:", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "interests_done", RegistrationState.interests)
async def process_interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    if not selected:
        await callback.answer("Выберите хотя бы один интерес!", show_alert=True)
        return
    await state.update_data(interests=", ".join(selected))
    await state.set_state(RegistrationState.games)
    await callback.message.delete()
    await callback.message.answer("Теперь выберите игры, в которые вы играете (можно несколько):", reply_markup=games_category_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("gamecat_"), RegistrationState.games)
async def process_games_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("gamecat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_games", [])
    await state.update_data(current_game_category=category)
    markup = games_items_keyboard(category, selected)
    await callback.message.edit_text(f"Выберите игры в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("game_"), RegistrationState.games)
async def process_game_item(callback: CallbackQuery, state: FSMContext):
    game = callback.data[len("game_"):]
    game = game.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_games", [])
    if game in selected:
        selected.remove(game)
        await callback.answer(f"Удалено: {game}")
    else:
        if len(selected) >= 10:
            await callback.answer("Максимум 10 игр.", show_alert=True)
            return
        selected.append(game)
        await callback.answer(f"Добавлено: {game}")
    await state.update_data(selected_games=selected)
    category = data.get("current_game_category", "")
    if category:
        markup = games_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "games_back", RegistrationState.games)
async def games_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категории игр:", reply_markup=games_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "games_none", RegistrationState.games)
async def games_none(callback: CallbackQuery, state: FSMContext):
    await state.update_data(games="Не играю")
    await state.set_state(RegistrationState.bio)
    await callback.message.delete()
    await callback.message.answer("Напишите немного о себе (био, до 500 символов):")
    await callback.answer()

@router.callback_query(F.data == "games_done", RegistrationState.games)
async def process_games_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_games", [])
    if not selected:
        await callback.answer("Выберите хотя бы одну игру или нажмите «Не играю».", show_alert=True)
        return
    await state.update_data(games=", ".join(selected))
    await state.set_state(RegistrationState.bio)
    await callback.message.delete()
    await callback.message.answer("Напишите немного о себе (био, до 500 символов):")
    await callback.answer()

@router.message(RegistrationState.bio)
async def process_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    if bio and len(bio) > 500:
        await message.answer("Био не может быть длиннее 500 символов.")
        return
    await state.update_data(bio=bio)
    await state.set_state(RegistrationState.photo)
    await message.answer("Отправьте ваше фото (можно пропустить, нажав кнопку «Пропустить»):",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Пропустить", callback_data="skip_photo")]
                         ]))

@router.callback_query(F.data == "skip_photo", RegistrationState.photo)
async def skip_photo(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await finish_registration(callback.message, state, session, callback.bot)
    await callback.answer()

@router.message(RegistrationState.photo)
async def process_photo(message: Message, state: FSMContext, session: AsyncSession):
    if not message.photo:
        await message.answer("Отправьте фото (или нажмите «Пропустить»).")
        return
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await finish_registration(message, state, session, message.bot)

async def finish_registration(message: Message, state: FSMContext, session: AsyncSession, bot):
    data = await state.get_data()
    ref_code = data.get("ref_code")

    user = User(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=data.get("name"),
        gender=data.get("gender"),
        age=data.get("age"),
        city=data.get("city"),
        favorite_genres=data.get("genres"),
        favorite_bands=data.get("bands"),
        favorite_songs=data.get("songs"),
        search_goal=data.get("goal"),
        interests=data.get("interests"),
        favorite_games=data.get("games"),
        bio=data.get("bio"),
        photo_file_id=data.get("photo_file_id")
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    if ref_code:
        referrer = await crud.get_user_by_referral_code(session, ref_code)
        if referrer and referrer.id != user.id:
            user.referred_by = referrer.id
            await session.commit()
            await crud.add_referral(session, referrer.id, user.id)
            try:
                await bot.send_message(
                    referrer.telegram_id,
                    f"🎉 Ваш друг {user.name or 'пользователь'} зарегистрировался по вашей ссылке! "
                    f"Ваша скидка теперь {referrer.referral_discount}%."
                )
            except:
                pass

    if not user.referral_code:
        user.referral_code = await crud.generate_referral_code(session, user.telegram_id)
        await session.commit()

    await state.clear()
    await message.answer(
        f"Регистрация завершена!\n\n"
        f"Ваша реферальная ссылка для приглашения друзей:\n"
        f"`t.me/MuseTwin_bot?start={user.referral_code}`\n\n"
        "Приводите друзей – получайте скидку до 90% на премиум!\n"
        "Каждый новый пользователь по вашей ссылке даёт +10% скидки (максимум 90%).",
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )