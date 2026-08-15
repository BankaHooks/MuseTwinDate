from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import likes_action_keyboard, main_menu_keyboard
from utils.helpers import format_user_card

router = Router()

from aiogram.fsm.state import State, StatesGroup

class LikesState(StatesGroup):
    current_index = State()
    likes_list = State()  

@router.callback_query(F.data == "likes")
async def likes_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    likes = await crud.get_likes_received(session, user.id)
    if not likes:
        await callback.message.edit_text("Вас пока никто не лайкнул.")
        await callback.answer()
        return
    like_ids = [like.from_user_id for like in likes]
    await state.update_data(likes_list=like_ids, current_index=0)
    await show_like(callback, state, session)

async def show_like(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    like_ids = data.get("likes_list", [])
    idx = data.get("current_index", 0)
    if idx >= len(like_ids):
        await callback.message.edit_text("Вы просмотрели все лайки.")
        await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        await state.clear()
        await callback.answer()
        return
    user_id = like_ids[idx]
    liker = await crud.get_user_by_id(session, user_id)
    if not liker:
        # если пользователь удалён, пропускаем
        await state.update_data(current_index=idx+1)
        await show_like(callback, state, session)
        return
    is_mutual = await crud.get_like_between(session, callback.from_user.id, liker.id)
    mutual = is_mutual is not None and is_mutual.is_mutual
    text = format_user_card(liker)
    if mutual:
        text += "\n✅ Взаимный лайк!"
    if liker.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=liker.photo_file_id, caption=text),
            reply_markup=likes_action_keyboard(liker.id)
        )
    else:
        await callback.message.edit_text(text, reply_markup=likes_action_keyboard(liker.id))
    await callback.answer()

@router.callback_query(F.data.startswith("likeback_"))
async def like_back_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    target_id = int(callback.data.split("_")[1])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    like = await crud.create_like(session, user.id, target_id)
    if like.is_mutual:
        target = await crud.get_user_by_id(session, target_id)
        await callback.bot.send_message(target.telegram_id,
            f"🎉 Взаимность! Вы и {user.name or user.username} понравились друг другу.")
        await callback.answer("Это взаимно! 🎉")
    else:
        await callback.answer("Вы лайкнули в ответ!")
    data = await state.get_data()
    idx = data.get("current_index", 0)
    await state.update_data(current_index=idx+1)
    await show_like(callback, state, session)

@router.callback_query(F.data.startswith("skip_like_"))
async def skip_like_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    idx = data.get("current_index", 0)
    await state.update_data(current_index=idx+1)
    await show_like(callback, state, session)

@router.callback_query(F.data == "likes_back")
async def likes_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()