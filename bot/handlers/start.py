from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.db import get_db
from states.registration import Registration
from keyboards.inline import main_menu_keyboard, genre_keyboard
from utils.helpers import validate_age
from utils.media import save_photo

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if user:
        await state.clear()
        await message.answer("Welcome back! Choose an option:", reply_markup=main_menu_keyboard())
        return
    await state.set_state(Registration.name)
    await message.answer("Let's register you!\nWhat's your name? (or type 'Skip')")

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    name = None if message.text.lower() == "skip" else message.text
    await state.update_data(name=name)
    await state.set_state(Registration.age)
    await message.answer("Your age? (18-99)")

@router.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    if not validate_age(message.text):
        await message.answer("Please enter age between 18 and 99.")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(Registration.city)
    await message.answer("City?")

@router.message(Registration.city)
async def reg_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Registration.genre)
    await message.answer("Favorite music genre?", reply_markup=genre_keyboard())

@router.callback_query(StateFilter(Registration.genre), F.data.startswith("genre_"))
async def reg_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split("_", 1)[1]
    await state.update_data(genre=genre)
    await state.set_state(Registration.bio)
    await callback.message.edit_text("Write a short bio:")
    await callback.answer()

@router.message(Registration.bio)
async def reg_bio(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.photo)
    await message.answer("Send a photo (or type 'Skip')")

@router.message(Registration.photo, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def reg_photo(message: Message, state: FSMContext, session: AsyncSession):
    photo_file_id = None
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        photo_file_id = photo.file_id
        await save_photo(photo, message.from_user.id)
    else:
        if message.text.lower() != "skip":
            await message.answer("Send photo or 'Skip'")
            return
    data = await state.get_data()
    user = await crud.create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=data.get("name"),
        age=data.get("age"),
        city=data.get("city"),
        genre=data.get("genre"),
        bio=data.get("bio"),
        photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer("Registration complete!", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Cancelled.")
    await callback.message.answer("Main menu:", reply_markup=main_menu_keyboard())
    await callback.answer()