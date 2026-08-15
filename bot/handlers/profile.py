from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.profile_edit import ProfileEdit
from keyboards.inline import profile_view_keyboard, genre_keyboard, gender_keyboard, main_menu_keyboard
from utils.helpers import validate_age, format_profile
from utils.media import save_photo
from utils.music_engine import resolve_tracks, engine, vector_to_json

router = Router()

EDIT_PROMPTS = {
    "name": "Введите новое имя (или 'Пропустить', чтобы оставить):",
    "age": "Введите новый возраст (18-99):",
    "city": "Введите новый город:",
    "band": "Введите любимую группу (или 'Пропустить'):",
    "bio": "Введите новое био:",
    "photo": "Отправьте новое фото (или 'Пропустить'):",
    "tracks": "Назовите 2-3 любимые песни через запятую (или 'Пропустить', чтобы оставить как есть):",
}


@router.callback_query(F.data == "profile")
async def profile_view(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    text = format_profile(user)
    await callback.message.delete()
    if user.photo_file_id:
        await callback.message.answer_photo(photo=user.photo_file_id, caption=text, reply_markup=profile_view_keyboard())
    else:
        await callback.message.answer(text, reply_markup=profile_view_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("edit_"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_", 1)[1]
    await callback.message.delete()
    if field == "genre":
        await state.set_state(ProfileEdit.genre)
        await callback.message.answer("Выберите жанр:", reply_markup=genre_keyboard())
    elif field == "gender":
        await state.set_state(ProfileEdit.gender)
        await callback.message.answer("Выберите пол партнера:", reply_markup=gender_keyboard())
    elif field in EDIT_PROMPTS:
        await state.set_state(getattr(ProfileEdit, field))
        await callback.message.answer(EDIT_PROMPTS[field])
    await callback.answer()


@router.message(ProfileEdit.name)
async def edit_name(message: Message, state: FSMContext, session: AsyncSession):
    name = None if message.text.lower() == "пропустить" else message.text
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, name=name)
    await state.clear()
    await message.answer("Имя обновлено!", reply_markup=main_menu_keyboard())


@router.message(ProfileEdit.age)
async def edit_age(message: Message, state: FSMContext, session: AsyncSession):
    if not validate_age(message.text):
        await message.answer("Неверный возраст. Введите 18-99.")
        return
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, age=int(message.text))
    await state.clear()
    await message.answer("Возраст обновлён!", reply_markup=main_menu_keyboard())


@router.message(ProfileEdit.city)
async def edit_city(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, city=message.text)
    await state.clear()
    await message.answer("Город обновлён!", reply_markup=main_menu_keyboard())


@router.callback_query(StateFilter(ProfileEdit.genre), F.data.startswith("genre_"))
async def edit_genre(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    genre = callback.data.split("_", 1)[1]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, genre=genre)
    await state.clear()
    await callback.message.edit_text("Жанр обновлён!", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(ProfileEdit.tracks)
async def edit_tracks(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if message.text.lower() == "пропустить":
        await state.clear()
        await message.answer("Оставили как было.", reply_markup=main_menu_keyboard())
        return
    names = message.text.split(",")
    matched, unmatched = resolve_tracks(names)
    if not matched:
        await message.answer("Ни одна песня не найдена. Попробуйте ещё раз или отправьте 'Пропустить'.")
        return
    indices = [m["index"] for m in matched]
    vector = engine.build_taste_vector(indices)
    tracks_display = "; ".join(f"{m['track_name']} — {m['artist']}" for m in matched)
    await crud.update_user(session, user, favorite_tracks=tracks_display, taste_vector=vector_to_json(vector))
    reply = "Любимые песни обновлены: " + tracks_display
    if unmatched:
        reply += "\nНе нашли: " + ", ".join(unmatched)
    await state.clear()
    await message.answer(reply, reply_markup=main_menu_keyboard())

@router.message(ProfileEdit.band)
async def edit_band(message: Message, state: FSMContext, session: AsyncSession):
    band = None if message.text.lower() == "пропустить" else message.text
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, favorite_band=band)
    await state.clear()
    await message.answer("Группа обновлена!", reply_markup=main_menu_keyboard())


@router.callback_query(StateFilter(ProfileEdit.gender), F.data.startswith("gender_"))
async def edit_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    gender = callback.data.split("_", 1)[1]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, preferred_gender=gender)
    await state.clear()
    await callback.message.edit_text("Пол партнера обновлён!", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(ProfileEdit.bio)
async def edit_bio(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, bio=message.text)
    await state.clear()
    await message.answer("Био обновлено!", reply_markup=main_menu_keyboard())


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
    await message.answer("Фото обновлено!", reply_markup=main_menu_keyboard())
