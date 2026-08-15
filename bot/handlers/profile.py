from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from states.profile_edit import ProfileEdit
from keyboards.inline import profile_view_keyboard, genre_keyboard, main_menu_keyboard
from utils.helpers import validate_age
from utils.media import save_photo

router = Router()

@router.callback_query(F.data == "profile")
async def profile_view(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Register first.")
        return
    text = f"👤 Your profile:\n"
    text += f"Name: {user.name or 'Not set'}\n"
    text += f"Age: {user.age or 'Not set'}\n"
    text += f"City: {user.city or 'Not set'}\n"
    text += f"Genre: {user.genre or 'Not set'}\n"
    text += f"Bio: {user.bio or 'Not set'}\n"
    text += f"Premium: {'✅' if user.is_premium else '❌'}"
    if user.photo_file_id:
        await callback.message.answer_photo(photo=user.photo_file_id, caption=text, reply_markup=profile_view_keyboard())
    else:
        await callback.message.edit_text(text, reply_markup=profile_view_keyboard())
    await callback.answer()

# Edit handlers
@router.callback_query(F.data.startswith("edit_"))
async def edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    if field == "name":
        await state.set_state(ProfileEdit.name)
        await callback.message.edit_text("Send new name (or 'Skip' to keep current):")
    elif field == "age":
        await state.set_state(ProfileEdit.age)
        await callback.message.edit_text("Send new age (18-99):")
    elif field == "city":
        await state.set_state(ProfileEdit.city)
        await callback.message.edit_text("Send new city:")
    elif field == "genre":
        await state.set_state(ProfileEdit.genre)
        await callback.message.edit_text("Choose genre:", reply_markup=genre_keyboard())
    elif field == "bio":
        await state.set_state(ProfileEdit.bio)
        await callback.message.edit_text("Send new bio:")
    elif field == "photo":
        await state.set_state(ProfileEdit.photo)
        await callback.message.edit_text("Send new photo (or 'Skip'):")
    await callback.answer()

@router.message(ProfileEdit.name)
async def edit_name(message: Message, state: FSMContext, session: AsyncSession):
    name = None if message.text.lower() == "skip" else message.text
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, name=name)
    await state.clear()
    await message.answer("Name updated!", reply_markup=main_menu_keyboard())

@router.message(ProfileEdit.age)
async def edit_age(message: Message, state: FSMContext, session: AsyncSession):
    if not validate_age(message.text):
        await message.answer("Invalid age. Enter 18-99.")
        return
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, age=int(message.text))
    await state.clear()
    await message.answer("Age updated!", reply_markup=main_menu_keyboard())

@router.message(ProfileEdit.city)
async def edit_city(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, city=message.text)
    await state.clear()
    await message.answer("City updated!", reply_markup=main_menu_keyboard())

@router.callback_query(StateFilter(ProfileEdit.genre), F.data.startswith("genre_"))
async def edit_genre(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    genre = callback.data.split("_", 1)[1]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.update_user(session, user, genre=genre)
    await state.clear()
    await callback.message.edit_text("Genre updated!", reply_markup=main_menu_keyboard())
    await callback.answer()

@router.message(ProfileEdit.bio)
async def edit_bio(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, bio=message.text)
    await state.clear()
    await message.answer("Bio updated!", reply_markup=main_menu_keyboard())

@router.message(ProfileEdit.photo, F.content_type.in_({ContentType.PHOTO, ContentType.TEXT}))
async def edit_photo(message: Message, state: FSMContext, session: AsyncSession):
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        file_id = photo.file_id
        await save_photo(photo, message.from_user.id)
    else:
        if message.text.lower() != "skip":
            await message.answer("Send photo or 'Skip'")
            return
        file_id = None
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.update_user(session, user, photo_file_id=file_id)
    await state.clear()
    await message.answer("Photo updated!", reply_markup=main_menu_keyboard())