from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.registration import Registration
from keyboards.inline import main_menu_keyboard, genre_keyboard, gender_keyboard
from utils.helpers import validate_age
from utils.media import save_photo
from utils.music_engine import resolve_tracks, engine, vector_to_json

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if user:
        await state.clear()
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu_keyboard())
        return
    await state.set_state(Registration.name)
    await message.answer("Давайте зарегистрируемся!\nКак вас зовут? (можно пропустить, отправив 'Пропустить')")

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    name = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(name=name)
    await state.set_state(Registration.age)
    await message.answer("Сколько вам лет? (18-99)")

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
    await state.update_data(city=message.text)
    await state.set_state(Registration.genre)
    await message.answer("Ваш любимый музыкальный жанр?", reply_markup=genre_keyboard())

@router.callback_query(StateFilter(Registration.genre), F.data.startswith("genre_"))
async def reg_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split("_", 1)[1]
    await state.update_data(genre=genre)
    await state.set_state(Registration.tracks)
    await callback.message.edit_text(
        "Назовите 2-3 любимые песни через запятую — так мы подберём вам пару со схожим вкусом.\n"
        "Например: Bohemian Rhapsody, Yesterday\n(или отправьте 'Пропустить')"
    )
    await callback.answer()

@router.message(Registration.tracks)
async def reg_tracks(message: Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(taste_vector=None, favorite_tracks=None)
        await state.set_state(Registration.band)
        await message.answer("А любимая группа/исполнитель? (можно пропустить, отправив 'Пропустить')")
        return
    names = message.text.split(",")
    matched, unmatched = resolve_tracks(names)
    if not matched:
        await message.answer("Ни одна песня не найдена в базе. Попробуйте ещё раз или отправьте 'Пропустить'.")
        return
    indices = [m["index"] for m in matched]
    vector = engine.build_taste_vector(indices)
    tracks_display = [f"{m['track_name']} — {m['artist']}" for m in matched]
    await state.update_data(taste_vector=vector_to_json(vector), favorite_tracks="; ".join(tracks_display))
    reply = "Нашли: " + ", ".join(tracks_display)
    if unmatched:
        reply += "\nНе нашли: " + ", ".join(unmatched)
    await message.answer(reply)
    await state.set_state(Registration.band)
    await message.answer("А любимая группа/исполнитель? (можно пропустить, отправив 'Пропустить')")

@router.message(Registration.band)
async def reg_band(message: Message, state: FSMContext):
    band = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(favorite_band=band)
    await state.set_state(Registration.preferred_gender)
    await message.answer("Кого вы ищете? (выберите пол)", reply_markup=gender_keyboard())

@router.callback_query(StateFilter(Registration.preferred_gender), F.data.startswith("gender_"))
async def reg_preferred_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_", 1)[1]
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
        age=data.get("age"),
        city=data.get("city"),
        genre=data.get("genre"),
        favorite_band=data.get("favorite_band"),
        favorite_tracks=data.get("favorite_tracks"),
        taste_vector=data.get("taste_vector"),
        preferred_gender=data.get("preferred_gender"),
        bio=data.get("bio"),
        photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer("Регистрация завершена!", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
