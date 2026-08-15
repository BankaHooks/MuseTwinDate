from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.crud import get_likes_count
from keyboards.inline import likes_action_keyboard
from keyboards.reply import main_reply_keyboard
from utils.helpers import format_user_card

router = Router()

class LikesState(StatesGroup):
    current_index = State()
    likes_list = State()

@router.callback_query(F.data == "likes")
async def likes_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await show_likes(callback.message, callback.from_user.id, state, session, delete_old=True)
    await callback.answer()

async def show_likes(target: Message, user_id: int, state: FSMContext, session: AsyncSession, delete_old: bool = False):
    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await target.answer("Зарегистрируйтесь через /start")
        return
    likes = await crud.get_likes_received(session, user.id)
    if not likes:
        await target.answer("Вас пока никто не лайкнул.", reply_markup=main_reply_keyboard())
        return
    like_ids = [like.from_user_id for like in likes]
    await state.update_data(likes_list=like_ids, current_index=0)
    await show_like_card(target, state, session)

async def show_like_card(target: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    like_ids = data.get("likes_list", [])
    idx = data.get("current_index", 0)
    if idx >= len(like_ids):
        await target.answer("Вы просмотрели все лайки.", reply_markup=main_reply_keyboard())
        await state.clear()
        return
    user_id = like_ids[idx]
    liker = await crud.get_user_by_id(session, user_id)
    if not liker:
        await state.update_data(current_index=idx+1)
        await show_like_card(target, state, session)
        return
    is_mutual = await crud.get_like_between(session, target.from_user.id, liker.id)
    mutual = is_mutual is not None and is_mutual.is_mutual
    text = format_user_card(liker)
    if mutual:
        text += "\nВзаимный лайк!"
    if liker.photo_file_id:
        await target.answer_photo(photo=liker.photo_file_id, caption=text, reply_markup=likes_action_keyboard(liker.id))
    else:
        await target.answer(text, reply_markup=likes_action_keyboard(liker.id))

async def show_likes_for_message(message: Message, state: FSMContext, session: AsyncSession):
    await show_likes(message, message.from_user.id, state, session, delete_old=False)

@router.callback_query(F.data.startswith("likeback_"))
async def like_back_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    target_id = int(callback.data.split("_")[1])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    target = await crud.get_user_by_id(session, target_id)
    if not target:
        await callback.answer("Пользователь не найден.")
        return
    like = await crud.create_like(session, user.id, target.id)
    # Уведомление о количестве лайков для цели
    total_likes = await get_likes_count(session, target.id)
    if total_likes > target.last_like_notification_count:
        count = total_likes
        if count == 1:
            text = "Вас лайкнул 1 человек."
        elif count in (2, 3, 4):
            text = f"Вас лайкнули {count} человека."
        else:
            text = f"Вас лайкнули {count} человек."
        await callback.bot.send_message(target.telegram_id, text)
        target.last_like_notification_count = count
        await session.commit()
    if like.is_mutual:
        user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
        target_link = f"@{target.username}" if target.username else f"[профиль](tg://user?id={target.telegram_id})"
        await callback.bot.send_message(
            target.telegram_id,
            f"Взаимный лайк! Вы и {user.name or user.username} понравились друг другу.\n"
            f"Напишите ему: {user_link}",
            parse_mode="Markdown"
        )
        await callback.bot.send_message(
            user.telegram_id,
            f"Взаимный лайк! Вы и {target.name or target.username} понравились друг другу.\n"
            f"Напишите ему: {target_link}",
            parse_mode="Markdown"
        )
        await callback.answer("Это взаимно!")
    else:
        await callback.answer("Вы лайкнули в ответ!")
    data = await state.get_data()
    idx = data.get("current_index", 0)
    await state.update_data(current_index=idx+1)
    await show_like_card(callback.message, state, session)

@router.callback_query(F.data.startswith("skip_like_"))
async def skip_like_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    idx = data.get("current_index", 0)
    await state.update_data(current_index=idx+1)
    await show_like_card(callback.message, state, session)

@router.callback_query(F.data == "likes_back")
async def likes_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await callback.answer()