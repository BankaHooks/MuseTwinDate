from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.registration import Registration
from keyboards.inline import (
    genre_choose_keyboard, gender_choose_keyboard, preferred_gender_keyboard,
    goal_keyboard, interest_category_keyboard, interest_items_keyboard, welcome_keyboard
)
from keyboards.reply import main_reply_keyboard
from utils.helpers import validate_age, normalize_city
from utils.media import save_photo
from utils.vk_api import enrich_profile_with_vk
from config import config

router = Router()

WELCOME_TEXT = (
    "Поздравляю, вы попали на запуск MuseTwinDate!\n\n"
    "Понимаем, что по началу трудно будет найти людей, но если вам интересна идея проекта, "
    "то, пожалуйста, не бросайте его и старайтесь иногда проверять не появились ли анкеты.\n\n"
    "А также в честь того, что вы участник первой 1000 пользователей, вы можете получить "
    "премиум статус, который с каждым обновлением будет давать всё больше функций — "
    "для этого напишите в лс @danhooks"
)

def truncate_field(text: str, max_len: int = 500) -> str:
    if not text:
        return text
    if len(text) > max_len:
        return text[:max_len].strip()
    return text

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if user:
        await state.clear()
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_reply_keyboard())
        return
    await state.set_state("welcome")
    await message.answer(WELCOME_TEXT, reply_markup=welcome_keyboard())

@router.callback_query(F.data == "welcome_start", StateFilter("welcome"))
async def welcome_start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await state.set_state(Registration.name)
    await callback.message.answer("Давайте зарегистрируемся!\nКак вас зовут? (можно пропустить, отправив 'Пропустить')")
    await callback.answer()

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    raw = message.text
    if raw.lower() == "пропустить":
        name = None
    else:
        name = truncate_field(raw, 100)
    await state.update_data(name=name)
    await state.set_state(Registration.gender)
    await message.answer("Укажите ваш пол:", reply_markup=gender_choose_keyboard())

@router.callback_query(StateFilter(Registration.gender), F.data.startswith("gender_"))
async def reg_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(Registration.age)
    await callback.message.edit_text("Сколько вам лет? (18-99)")
    await callback.answer()

@router.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    if not validate_age(message.text):
        await message.answer("Пожалуйста, введите возраст от 18 до 99.")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(Registration.city)
    await message.answer("В каком городе вы живёте?")

@router.message(Registration.city)
async def reg_city(message: Message, state: FSMContext):
    city = normalize_city(message.text)
    await state.update_data(city=city)
    await state.set_state(Registration.genres)
    await message.answer("Выберите ваши любимые жанры (можно несколько):", reply_markup=genre_choose_keyboard())

@router.callback_query(StateFilter(Registration.genres), F.data.startswith("genre_add_"))
async def reg_add_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split("_")[2]
    data = await state.get_data()
    genres = data.get("genres", [])
    if genre not in genres:
        genres.append(genre)
    await state.update_data(genres=genres)
    await callback.answer(f"Добавлен жанр: {genre}")

@router.callback_query(StateFilter(Registration.genres), F.data == "genres_done")
async def reg_genres_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    genres = data.get("genres", [])
    if not genres:
        await callback.answer("Выберите хотя бы один жанр.", show_alert=True)
        return
    joined = ", ".join(genres)
    await state.update_data(genres=truncate_field(joined, 500))
    await state.set_state(Registration.bands)
    await callback.message.edit_text("Введите ваши любимые группы (до 5, разделённых запятой):\n(или 'Пропустить')")
    await callback.answer()

@router.message(Registration.bands)
async def reg_bands(message: Message, state: FSMContext):
    bands_text = message.text.strip()
    if bands_text.lower() == "пропустить":
        await state.update_data(bands=None)
    else:
        bands = [b.strip() for b in bands_text.split(",") if b.strip()]
        if len(bands) > 5:
            await message.answer("Можно ввести не более 5 групп. Попробуйте снова или отправьте 'Пропустить'.")
            return
        joined = ", ".join(bands)
        await state.update_data(bands=truncate_field(joined, 500))
    await state.set_state(Registration.songs)
    await message.answer("Введите ваши любимые песни (можно несколько, через запятую):\n(или 'Пропустить')")

@router.message(Registration.songs)
async def reg_songs(message: Message, state: FSMContext):
    songs = None if message.text.lower() == "пропустить" else truncate_field(message.text, 500)
    await state.update_data(songs=songs)
    await state.set_state(Registration.goal)
    await message.answer("Какова ваша цель знакомства?", reply_markup=goal_keyboard())

@router.callback_query(StateFilter(Registration.goal), F.data.startswith("goal_"))
async def reg_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split("_")[1]
    await state.update_data(goal=goal)
    await state.set_state(Registration.interests)
    await callback.message.edit_text("Выберите категорию интересов, затем тему. Можно выбрать до 10 тем.", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(Registration.interests), F.data.startswith("cat_"))
async def reg_show_interests(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1].replace("_", " ")
    data = await state.get_data()
    selected = data.get("interests_list", [])
    await state.update_data(current_category=category)
    await callback.message.edit_text(f"Выберите темы из категории «{category}» (до 10):", reply_markup=interest_items_keyboard(category, selected))
    await callback.answer()

@router.callback_query(StateFilter(Registration.interests), F.data.startswith("interest_"))
async def reg_toggle_interest(callback: CallbackQuery, state: FSMContext):
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

@router.callback_query(StateFilter(Registration.interests), F.data == "interests_back")
async def reg_interests_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите категорию интересов:", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(Registration.interests), F.data == "interests_done")
async def reg_interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("interests_list", [])
    if selected:
        joined = ", ".join(selected)
        await state.update_data(interests=truncate_field(joined, 500))
    else:
        await state.update_data(interests=None)
    await state.set_state(Registration.preferred_gender)
    await callback.message.edit_text("Кого вы ищете? (выберите пол)", reply_markup=preferred_gender_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(Registration.preferred_gender), F.data.startswith("pref_gender_"))
async def reg_preferred_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[2]
    await state.update_data(preferred_gender=gender)
    await state.set_state(Registration.bio)
    await callback.message.edit_text("Расскажите немного о себе (био):")
    await callback.answer()

@router.message(Registration.bio)
async def reg_bio(message: Message, state: FSMContext):
    bio = truncate_field(message.text, 500)
    await state.update_data(bio=bio)
    await state.set_state(Registration.photo)
    await message.answer("Отправьте фото (или 'Пропустить')")

@router.message(Registration.photo, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def reg_photo(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user_id = data.get("user_id")
    photo_file_id = None
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        photo_file_id = photo.file_id
        await save_photo(photo, message.from_user.id)
    else:
        if message.text.lower() != "пропустить":
            await message.answer("Отправьте фото или 'Пропустить'")
            return
    if user_id:
        user = await crud.get_user_by_id(session, user_id)
        if user:
            await crud.update_user(
                session, user,
                name=data.get("name"),
                gender=data.get("gender"),
                age=data.get("age"),
                city=data.get("city"),
                favorite_genres=data.get("genres"),
                favorite_bands=data.get("bands"),
                favorite_songs=data.get("songs"),
                search_goal=data.get("goal"),
                interests=data.get("interests"),
                preferred_gender=data.get("preferred_gender"),
                bio=data.get("bio"),
                photo_file_id=photo_file_id,
            )
            if config.VK_ACCESS_TOKEN:
                await enrich_profile_with_vk(user, session, config.VK_ACCESS_TOKEN)
            await message.answer("Профиль обновлён!", reply_markup=main_reply_keyboard())
    else:
        user = await crud.create_user(
            session,
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
            preferred_gender=data.get("preferred_gender"),
            bio=data.get("bio"),
            photo_file_id=photo_file_id,
        )
        if config.VK_ACCESS_TOKEN:
            await enrich_profile_with_vk(user, session, config.VK_ACCESS_TOKEN)
        await message.answer("Регистрация завершена!", reply_markup=main_reply_keyboard())
    await state.clear()
    await message.answer(
    "✅ Регистрация завершена!\n\n"
    "🔗 Вы также можете привязать VK для более точного подбора по музыкальным предпочтениям.\n"
    "Для этого зайдите в профиль → Редактировать профиль → Импорт из VK. \n" \
    "А также в профиле мы можете выключить анкету, и сменить режим поиска (по всей стране/только в своем городе) \n" \
    "[Настоятельно рекомендуется использовать поиск по всей стране на время запуска бота]"
    )   

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await callback.answer()