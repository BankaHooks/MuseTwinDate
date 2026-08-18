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
from utils.security import escape_markdown
import logging

logger = logging.getLogger(__name__)
router = Router()

class LikesState(StatesGroup):
    current_index = State()
    likes_list = State()
    viewer_id = State()

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
        if delete_old:
            await target.delete()
        await target.answer("Вас пока никто не лайкнул.", reply_markup=main_reply_keyboard())
        return
    like_ids = [like.from_user_id for like in likes]
    await state.update_data(likes_list=like_ids, current_index=0, viewer_id=user.id)
    if delete_old:
        await target.delete()
    await show_like_card(target, state, session, edit=False)

async def show_like_card(target: Message, state: FSMContext, session: AsyncSession, edit: bool = False):
    data = await state.get_data()
    like_ids = data.get("likes_list", [])
    idx = data.get("current_index", 0)
    viewer_id = data.get("viewer_id")
    if idx >= len(like_ids):
        if edit:
            await target.delete()
            await target.answer("Вы просмотрели все лайки.", reply_markup=main_reply_keyboard())
        else:
            await target.answer("Вы просмотрели все лайки.", reply_markup=main_reply_keyboard())
        await state.clear()
        return
    user_id = like_ids[idx]
    liker = await crud.get_user_by_id(session, user_id)
    if not liker:
        await state.update_data(current_index=idx + 1)
        await show_like_card(target, state, session, edit=edit)
        return
    like_between = await crud.get_like_between(session, viewer_id, liker.id) if viewer_id else None
    mutual = like_between is not None and like_between.is_mutual
    text = format_user_card(liker)
    if mutual:
        text += "\n✅ Взаимный лайк!"
    markup = likes_action_keyboard(liker.id)
    if edit:
        if liker.photo_file_id:
            await target.edit_media(InputMediaPhoto(media=liker.photo_file_id, caption=text), reply_markup=markup)
        else:
            await target.edit_text(text, reply_markup=markup)
    else:
        if liker.photo_file_id:
            await target.answer_photo(photo=liker.photo_file_id, caption=text, reply_markup=markup)
        else:
            await target.answer(text, reply_markup=markup)

async def show_likes_for_message(message: Message, state: FSMContext, session: AsyncSession):
    await show_likes(message, message.from_user.id, state, session, delete_old=False)

@router.callback_query(F.data.startswith("likeback_"))
async def like_back_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    target_id = int(callback.data.split("_")[1])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    target = await crud.get_user_by_id(session, target_id)
    if not target:
        await callback.answer("Пользователь не найден.")
        return
    if not await crud.can_like(session, user):
        await callback.answer("Вы исчерпали лимит лайков на сегодня (30). Купите премиум!", show_alert=True)
        return

    like = await crud.create_like(session, user.id, target.id)
    await crud.increment_likes(session, user)

    total_likes = await get_likes_count(session, target.id)
    if total_likes > target.last_like_notification_count:
        count = total_likes
        display_count = "9+" if count > 9 else str(count)
        if count == 1:
            text = "Вас лайкнул 1 человек."
        elif 2 <= count <= 4:
            text = f"Вас лайкнули {display_count} человека."
        else:
            text = f"Вас лайкнули {display_count} человек."
        try:
            await callback.bot.send_message(target.telegram_id, text)
            target.last_like_notification_count = count
            await session.commit()
        except Exception as e:
            if "blocked" in str(e).lower():
                await crud.set_user_blocked_bot(session, target.id)
            # Игнорируем другие ошибки

    if like.is_mutual:
        safe_user_name = escape_markdown(user.name or user.username or "Пользователь")
        safe_target_name = escape_markdown(target.name or target.username or "Пользователь")
        user_link = f"@{user.username}" if user.username else f"профиль (tg://user?id={user.telegram_id})"
        target_link = f"@{target.username}" if target.username else f"профиль (tg://user?id={target.telegram_id})"
        try:
            await callback.bot.send_message(
                target.telegram_id,
                f"💞 Взаимный лайк! Вы и {safe_user_name} понравились друг другу.\nНапишите ему: {user_link}"
            )
        except Exception as e:
            if "blocked" in str(e).lower():
                await crud.set_user_blocked_bot(session, target.id)
            else:
                logger.error(f"Failed to send mutual like to target {target.telegram_id}: {e}")
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"💞 Взаимный лайк! Вы и {safe_target_name} понравились друг другу.\nНапишите ему: {target_link}"
            )
        except Exception as e:
            if "blocked" in str(e).lower():
                await crud.set_user_blocked_bot(session, user.id)
            else:
                logger.error(f"Failed to send mutual like to user {user.telegram_id}: {e}")
        await callback.answer("Это взаимно! 💞")
    else:
        await callback.answer("Вы лайкнули в ответ!")

    await show_likes(callback.message, callback.from_user.id, state, session, delete_old=True)

@router.callback_query(F.data.startswith("skip_like_"))
async def skip_like(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    target_id = int(callback.data.split("_")[2])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        await crud.create_skip(session, user.id, target_id)
    data = await state.get_data()
    idx = data.get("current_index", 0)
    await state.update_data(current_index=idx + 1)
    await show_like_card(callback.message, state, session, edit=True)
    await callback.answer()

@router.callback_query(F.data == "likes_back")
async def likes_back(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await callback.answer()