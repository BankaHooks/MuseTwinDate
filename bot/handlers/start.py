from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.registration import Registration
from keyboards.inline import genre_keyboard, gender_keyboard, gender_choose_keyboard, preferred_gender_keyboard
from keyboards.reply import main_reply_keyboard
from utils.helpers import validate_age, normalize_city
from utils.media import save_photo

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if user:
        await state.clear()
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_reply_keyboard())
        return
    await state.set_state(Registration.name)
    await message.answer("Давайте зарегистрируемся!\nКак вас зовут? (можно пропустить, отправив 'Пропустить')")

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    name = None if message.text.lower() == "пропустить" else message.text
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
    await state.set_state(Registration.genre)
    await message.answer("Ваш любимый музыкальный жанр?", reply_markup=genre_keyboard())

@router.callback_query(StateFilter(Registration.genre), F.data.startswith("genre_"))
async def reg_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split("_", 1)[1]
    await state.update_data(genre=genre)
    await state.set_state(Registration.songs)
    await callback.message.edit_text(
        "Введите ваши любимые песни (можно несколько, через запятую).\n"
        "Это поможет нам найти людей с похожим вкусом.\n(или отправьте 'Пропустить')"
    )
    await callback.answer()

@router.message(Registration.songs)
async def reg_songs(message: Message, state: FSMContext):
    songs = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(favorite_songs=songs)
    await state.set_state(Registration.band)
    await message.answer("А любимая группа/исполнитель? (можно пропустить, отправив 'Пропустить')")

@router.message(Registration.band)
async def reg_band(message: Message, state: FSMContext):
    band = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(favorite_band=band)
    await state.set_state(Registration.preferred_gender)
    await message.answer("Кого вы ищете? (выберите пол)", reply_markup=preferred_gender_keyboard())

@router.callback_query(StateFilter(Registration.preferred_gender), F.data.startswith("pref_gender_"))
async def reg_preferred_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[2]
    await state.update_data(preferred_gender=gender)
    await state.set_state(Registration.bio)
    await callback.message.edit_text("Расскажите немного о себе (био):")
    await callback.answer()

@router.message(Registration.bio)
async def reg_bio(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.photo)
    await message.answer("Отправьте фото (или 'Пропустить')")

@router.message(Registration.photo, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def reg_photo(message: Message, state: FSMContext, session: AsyncSession):
    photo_file_id = None
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        photo_file_id = photo.file_id
        await save_photo(photo, message.from_user.id)
    else:
        if message.text.lower() != "пропустить":
            await message.answer("Отправьте фото или 'Пропустить'")
            return
    data = await state.get_data()
    await crud.create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=data.get("name"),
        gender=data.get("gender"),
        age=data.get("age"),
        city=data.get("city"),
        genre=data.get("genre"),
        favorite_band=data.get("favorite_band"),
        favorite_songs=data.get("favorite_songs"),
        preferred_gender=data.get("preferred_gender"),
        bio=data.get("bio"),
        photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer("Регистрация завершена!", reply_markup=main_reply_keyboard())

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await callback.answer()