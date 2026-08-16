from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.registration import Registration
from states.profile_edit import ProfileEdit
from keyboards.inline import (
    profile_main_keyboard, profile_edit_keyboard, profile_search_settings_keyboard,
    genre_choose_keyboard, gender_choose_keyboard, preferred_gender_keyboard,
    goal_keyboard, interest_category_keyboard, interest_items_keyboard, main_menu_keyboard
)
from keyboards.reply import main_reply_keyboard
from utils.helpers import validate_age, format_profile, normalize_city
from utils.media import save_photo
from utils.security import escape_markdown
from utils.vk_api import enrich_profile_with_vk
from config import config

router = Router()

def truncate_field(text: str, max_len: int = 500) -> str:
    if not text:
        return text
    if len(text) > max_len:
        return text[:max_len].strip()
    return text

@router.callback_query(F.data == "profile")
async def profile_view(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return

    received = await crud.get_likes_count(session, user.id)
    given = await crud.get_likes_given_count(session, user.id)
    mutual = await crud.get_mutual_likes_count(session, user.id)

    text = format_profile(user)
    text += f"\n\n📊 Статистика лайков:\n"
    text += f"Получено: {received}\n"
    text += f"Отправлено: {given}\n"
    text += f"Взаимных: {mutual}"

    await callback.message.delete()
    if user.photo_file_id:
        await callback.message.answer_photo(photo=user.photo_file_id, caption=text, reply_markup=profile_main_keyboard())
    else:
        await callback.message.answer(text, reply_markup=profile_main_keyboard())
    await callback.answer()

async def show_profile_for_message(message: Message, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Зарегистрируйтесь через /start")
        return

    received = await crud.get_likes_count(session, user.id)
    given = await crud.get_likes_given_count(session, user.id)
    mutual = await crud.get_mutual_likes_count(session, user.id)

    text = format_profile(user)
    text += f"\n\n📊 Статистика лайков:\n"
    text += f"Получено: {received}\n"
    text += f"Отправлено: {given}\n"
    text += f"Взаимных: {mutual}"

    if user.photo_file_id:
        await message.answer_photo(photo=user.photo_file_id, caption=text, reply_markup=profile_main_keyboard())
    else:
        await message.answer(text, reply_markup=profile_main_keyboard())

@router.callback_query(F.data == "profile_back")
async def profile_back(callback: CallbackQuery, session: AsyncSession):
    await profile_view(callback, session)

@router.callback_query(F.data == "profile_edit_menu")
async def profile_edit_menu(callback: CallbackQuery):
    text = "Выберите поле для редактирования:"
    markup = profile_edit_keyboard()
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=markup)
    else:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "profile_search_settings")
async def profile_search_settings(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    text = "Настройки поиска:"
    markup = profile_search_settings_keyboard(user)
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=markup)
    else:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "reset_profile")
async def reset_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    await state.update_data(user_id=user.id)
    fields = [
        "name", "gender", "age", "city", "favorite_genres", "favorite_bands",
        "favorite_songs", "favorite_albums", "favorite_artists", "search_goal",
        "interests", "preferred_gender", "bio", "photo_file_id"
    ]
    for field in fields:
        setattr(user, field, None)
    await session.commit()
    await state.set_state(Registration.name)
    await callback.message.delete()
    await callback.message.answer("Начнем заполнение профиля заново. Как вас зовут? (можно пропустить, отправив 'Пропустить')")
    await callback.answer()

@router.callback_query(F.data == "toggle_city")
async def toggle_city(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    user.search_city_only = not user.search_city_only
    await session.commit()
    await profile_search_settings(callback, session)

@router.callback_query(F.data == "toggle_hide")
async def toggle_hide(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    user.is_hidden = not user.is_hidden
    await session.commit()
    await profile_search_settings(callback, session)

@router.callback_query(F.data.startswith("edit_"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_", 1)[1]
    await callback.message.delete()
    if field == "genres":
        await state.set_state(ProfileEdit.genres)
        await callback.message.answer("Выберите ваши жанры (можно несколько):", reply_markup=genre_choose_keyboard())
    elif field == "bands":
        await state.set_state(ProfileEdit.bands)
        await callback.message.answer("Введите ваши любимые группы (до 5, через запятую):")
    elif field == "songs":
        await state.set_state(ProfileEdit.songs)
        await callback.message.answer("Введите ваши любимые песни (можно несколько, через запятую):")
    elif field == "albums":
        await state.set_state(ProfileEdit.albums)
        await callback.message.answer("Введите ваши любимые альбомы (можно несколько, через запятую):")
    elif field == "artists":
        await state.set_state(ProfileEdit.artists)
        await callback.message.answer("Введите ваших любимых исполнителей (можно несколько, через запятую):")
    elif field == "goal":
        await state.set_state(ProfileEdit.goal)
        await callback.message.answer("Какова ваша цель знакомства?", reply_markup=goal_keyboard())
    elif field == "interests":
        await state.set_state(ProfileEdit.interests)
        await callback.message.answer("Выберите категорию интересов, затем тему. Можно выбрать до 10 тем.", reply_markup=interest_category_keyboard())
    elif field == "gender":
        await state.set_state(ProfileEdit.gender)
        await callback.message.answer("Выберите ваш пол:", reply_markup=gender_choose_keyboard())
    elif field == "preferred_gender":
        await state.set_state(ProfileEdit.preferred_gender)
        await callback.message.answer("Кого вы ищете?", reply_markup=preferred_gender_keyboard())
    else:
        prompts = {
            "name": "Введите новое имя (или 'Пропустить', чтобы оставить):",
            "age": "Введите новый возраст (18-99):",
            "city": "Введите новый город:",
            "bio": "Введите новое био:",
            "photo": "Отправьте новое фото (или 'Пропустить'):",
        }
        if field in prompts:
            await state.set_state(getattr(ProfileEdit, field))
            await callback.message.answer(prompts[field])
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.genres), F.data.startswith("genre_add_"))
async def edit_add_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split("_")[2]
    data = await state.get_data()
    genres = data.get("genres", [])
    if genre not in genres:
        genres.append(genre)
    await state.update_data(genres=genres)
    await callback.answer(f"Добавлен жанр: {genre}")

@router.callback_query(StateFilter(ProfileEdit.genres), F.data == "genres_done")
async def edit_genres_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    genres = data.get("genres", [])
    if not genres:
        await callback.answer("Выберите хотя бы один жанр.", show_alert=True)
        return
    genre_str = ", ".join(genres)
    genre_str = truncate_field(genre_str, 500)
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, favorite_genres=genre_str)
    await state.clear()
    await callback.message.edit_text("Жанры обновлены", reply_markup=main_reply_keyboard())
    await callback.answer()

@router.message(ProfileEdit.bands)
async def edit_bands(message: Message, state: FSMContext, session: AsyncSession):
    bands_text = message.text.strip()
    if bands_text.lower() == "пропустить":
        bands = None
    else:
        bands = [b.strip() for b in bands_text.split(",") if b.strip()]
        if len(bands) > 5:
            await message.answer("Можно ввести не более 5 групп. Попробуйте снова или отправьте 'Пропустить'.")
            return
        bands = ", ".join(bands)
        bands = truncate_field(bands, 500)
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, favorite_bands=bands)
    if config.VK_ACCESS_TOKEN:
        await enrich_profile_with_vk(user, session, config.VK_ACCESS_TOKEN)
    await state.clear()
    await message.answer("Группы обновлены", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.songs)
async def edit_songs(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    songs = None if message.text.lower() == "пропустить" else truncate_field(message.text, 500)
    await crud.update_user(session, user, favorite_songs=songs)
    await state.clear()
    await message.answer("Песни обновлены", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.albums)
async def edit_albums(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    albums = None if message.text.lower() == "пропустить" else truncate_field(message.text, 500)
    await crud.update_user(session, user, favorite_albums=albums)
    await state.clear()
    await message.answer("Альбомы обновлены", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.artists)
async def edit_artists(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    artists = None if message.text.lower() == "пропустить" else truncate_field(message.text, 500)
    await crud.update_user(session, user, favorite_artists=artists)
    await state.clear()
    await message.answer("Исполнители обновлены", reply_markup=main_reply_keyboard())

@router.callback_query(StateFilter(ProfileEdit.goal), F.data.startswith("goal_"))
async def edit_goal(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    goal = callback.data.split("_")[1]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, search_goal=goal)
    await state.clear()
    await callback.message.edit_text("Цель обновлена", reply_markup=main_reply_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.interests), F.data.startswith("cat_"))
async def edit_show_interests(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1].replace("_", " ")
    data = await state.get_data()
    selected = data.get("interests_list", [])
    await state.update_data(current_category=category)
    await callback.message.edit_text(f"Выберите темы из категории «{category}» (до 10):", reply_markup=interest_items_keyboard(category, selected))
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.interests), F.data.startswith("interest_"))
async def edit_toggle_interest(callback: CallbackQuery, state: FSMContext):
    topic = callback.data.split("_", 1)[1].replace("_", " ")
    data = await state.get_data()
    selected = data.get("interests_list", [])
    if topic in selected:
        selected.remove(topic)
        await callback.answer(f"Убрано: {topic}")
    else:
        if len(selected) >= 10:
            await callback.answer("Можно выбрать не более 10 тем.", show_alert=True)
            return
        selected.append(topic)
        await callback.answer(f"Добавлено: {topic}")
    await state.update_data(interests_list=selected)
    category = data.get("current_category")
    if category:
        await callback.message.edit_text(f"Выберите темы из категории «{category}» (до 10):", reply_markup=interest_items_keyboard(category, selected))
    else:
        await callback.message.edit_text("Выберите категорию:", reply_markup=interest_category_keyboard())

@router.callback_query(StateFilter(ProfileEdit.interests), F.data == "interests_back")
async def edit_interests_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категорию интересов:", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.interests), F.data == "interests_done")
async def edit_interests_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected = data.get("interests_list", [])
    interest_str = ", ".join(selected) if selected else None
    if interest_str:
        interest_str = truncate_field(interest_str, 500)
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, interests=interest_str)
    await state.clear()
    await callback.message.edit_text("Интересы обновлены", reply_markup=main_reply_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.gender), F.data.startswith("gender_"))
async def process_edit_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    gender = callback.data.split("_")[1]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, gender=gender)
    await state.clear()
    await callback.message.edit_text("Пол обновлён", reply_markup=main_reply_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(ProfileEdit.preferred_gender), F.data.startswith("pref_gender_"))
async def process_edit_preferred_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    gender = callback.data.split("_")[2]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, preferred_gender=gender)
    await state.clear()
    await callback.message.edit_text("Предпочтения обновлены", reply_markup=main_reply_keyboard())
    await callback.answer()

@router.message(ProfileEdit.name)
async def edit_name(message: Message, state: FSMContext, session: AsyncSession):
    if message.text.lower() == "пропустить":
        name = None
    else:
        name = truncate_field(message.text, 100)
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, name=name)
    await state.clear()
    await message.answer("Имя обновлено", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.age)
async def edit_age(message: Message, state: FSMContext, session: AsyncSession):
    if not validate_age(message.text):
        await message.answer("Неверный возраст. Введите 18-99.")
        return
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, age=int(message.text))
    await state.clear()
    await message.answer("Возраст обновлён", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.city)
async def edit_city(message: Message, state: FSMContext, session: AsyncSession):
    city = normalize_city(message.text)
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, city=city)
    await state.clear()
    await message.answer("Город обновлён", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.bio)
async def edit_bio(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    bio = truncate_field(message.text, 500)
    await crud.update_user(session, user, bio=bio)
    await state.clear()
    await message.answer("Био обновлено", reply_markup=main_reply_keyboard())

@router.message(ProfileEdit.photo, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def edit_photo(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        await save_photo(photo, message.from_user.id)
        await crud.update_user(session, user, photo_file_id=photo.file_id)
    else:
        if message.text.lower() != "пропустить":
            await message.answer("Отправьте фото или 'Пропустить'")
            return
    await state.clear()
    await message.answer("Фото обновлено", reply_markup=main_reply_keyboard())

@router.callback_query(F.data == "refresh_recommendations")
async def refresh_recommendations(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    if not config.VK_ACCESS_TOKEN:
        await callback.answer("Функция временно недоступна.", show_alert=True)
        return
    if not user.favorite_bands:
        await callback.answer("У вас нет любимых групп.", show_alert=True)
        return
    await callback.message.edit_text("Ищем рекомендации...")
    similar = await enrich_profile_with_vk(user, session, config.VK_ACCESS_TOKEN)
    if similar:
        await callback.message.edit_text(
            f"Рекомендуем добавить: {', '.join(similar)}\nОбновлено в профиле.",
            reply_markup=profile_edit_keyboard()
        )
    else:
        await callback.message.edit_text("Не удалось найти рекомендации.")
    await callback.answer()