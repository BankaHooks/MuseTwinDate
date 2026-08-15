from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import likes_action_keyboard
from keyboards.reply import main_reply_keyboard
from utils.helpers import format_user_card

router = Router()

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
        await callback.message.edit_text("Вас пока никто не лайкнул.", reply_markup=main_reply_keyboard())
        await callback.answer()
        return
    like_ids = [like.from_user_id for like in likes]
    await state.update_data(likes_list=like_ids, current_index=0)
    await show_like(callback, state, session)

@router.message(F.text == "❤️ Лайки")
async def likes_button_handler(message: Message, state: FSMContext, session: AsyncSession):
    fake_callback = CallbackQuery(
        id="fake",
        from_user=message.from_user,
        message=message,
        chat_instance="fake",
        data="likes",
    )
    await likes_start(fake_callback, state, session)

async def show_like(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    like_ids = data.get("likes_list", [])
    idx = data.get("current_index", 0)
    if idx >= len(like_ids):
        await callback.message.edit_text("Вы просмотрели все лайки.", reply_markup=main_reply_keyboard())
        await state.clear()
        await callback.answer()
        return
    user_id = like_ids[idx]
    liker = await crud.get_user_by_id(session, user_id)
    if not liker:
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
    target = await crud.get_user_by_id(session, target_id)
    if not target:
        await callback.answer("Пользователь не найден.")
        return
    like = await crud.create_like(session, user.id, target.id)
    if like.is_mutual:
        user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
        target_link = f"@{target.username}" if target.username else f"[профиль](tg://user?id={target.telegram_id})"
        await callback.bot.send_message(
            target.telegram_id,
            f"🎉 Взаимный лайк! Вы и {user.name or user.username} понравились друг другу.\n"
            f"Напишите ему: {user_link}",
            parse_mode="Markdown"
        )
        await callback.bot.send_message(
            user.telegram_id,
            f"🎉 Взаимный лайк! Вы и {target.name or target.username} понравились друг другу.\n"
            f"Напишите ему: {target_link}",
            parse_mode="Markdown"
        )
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
    await callback.message.edit_text("Главное меню:", reply_markup=main_reply_keyboard())
    await callback.answer()