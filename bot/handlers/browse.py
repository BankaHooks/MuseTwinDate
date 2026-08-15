from typing import Union
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.crud import get_likes_count
from keyboards.inline import browse_actions_keyboard, report_reason_keyboard, profile_actions_keyboard
from keyboards.reply import main_reply_keyboard
from states.browse import Browse
from utils.helpers import format_user_card
from utils.matching import pick_candidate_simple

router = Router()

async def show_candidate(event: Union[Message, CallbackQuery], state: FSMContext, session: AsyncSession):
    user_id = event.from_user.id
    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await event.answer("Зарегистрируйтесь через /start")
        return
    candidate, score = await pick_candidate_simple(session, user)
    if not candidate:
        await event.answer("Нет больше анкет для показа.", reply_markup=main_reply_keyboard())
        return
    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)
    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    if candidate.photo_file_id:
        await event.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
    else:
        await event.answer(text, reply_markup=markup)

@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, session: AsyncSession):
    await show_candidate(message, state, session)

@router.message(F.text == "Поиск")
async def search_button_handler(message: Message, state: FSMContext, session: AsyncSession):
    await search_command(message, state, session)

@router.callback_query(F.data == "browse")
async def browse_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await show_candidate(callback.message, state, session)
    await callback.answer()

@router.callback_query(F.data == "like", Browse.candidate_id)
async def like_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Нет анкеты.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not await crud.can_like(session, user):
        await callback.answer("Вы исчерпали лимит лайков на сегодня (30). Купите премиум!", show_alert=True)
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Анкета не найдена.")
        await state.clear()
        return
    like = await crud.create_like(session, user.id, candidate.id)
    await crud.increment_likes(session, user)

    # Уведомление о количестве лайков для цели
    total_likes = await get_likes_count(session, candidate.id)
    if total_likes > candidate.last_like_notification_count:
        count = total_likes
        if count == 1:
            text = "Вас лайкнул 1 человек."
        elif count in (2, 3, 4):
            text = f"Вас лайкнули {count} человека."
        else:
            text = f"Вас лайкнули {count} человек."
        await callback.bot.send_message(candidate.telegram_id, text)
        candidate.last_like_notification_count = count
        await session.commit()

    if like.is_mutual:
        user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
        candidate_link = f"@{candidate.username}" if candidate.username else f"[профиль](tg://user?id={candidate.telegram_id})"
        await callback.bot.send_message(
            candidate.telegram_id,
            f"Взаимный лайк! Вы и {user.name or user.username} понравились друг другу.\n"
            f"Напишите ему: {user_link}",
            parse_mode="Markdown"
        )
        await callback.bot.send_message(
            user.telegram_id,
            f"Взаимный лайк! Вы и {candidate.name or candidate.username} понравились друг другу.\n"
            f"Напишите ему: {candidate_link}",
            parse_mode="Markdown"
        )
        await callback.answer("Это взаимно!")
    else:
        await callback.answer("Лайк поставлен!")
    await show_next(callback, state, session)

@router.callback_query(F.data == "skip", Browse.candidate_id)
async def skip_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if candidate_id:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        await crud.create_skip(session, user.id, candidate_id)
    await show_next(callback, state, session)

@router.callback_query(F.data == "report_user", Browse.candidate_id)
async def report_user(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Нет анкеты.")
        return
    await state.update_data(report_target=candidate_id)
    if callback.message.photo:
        await callback.message.edit_caption(
            caption="Выберите причину жалобы:",
            reply_markup=report_reason_keyboard()
        )
    else:
        await callback.message.edit_text(
            text="Выберите причину жалобы:",
            reply_markup=report_reason_keyboard()
        )
    await callback.answer()

@router.callback_query(F.data.startswith("reportreason_"))
async def report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    reason = callback.data.split("_", 1)[1]
    data = await state.get_data()
    target_id = data.get("report_target")
    if not target_id:
        await callback.answer("Ошибка: цель не найдена.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.create_report(session, user.id, target_id, reason)
    await callback.answer("Жалоба отправлена. Спасибо.", show_alert=True)
    await state.update_data(report_target=None)
    await show_next(callback, state, session)

async def show_next(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    candidate, score = await pick_candidate_simple(session, user)
    if not candidate:
        await callback.message.edit_text("Нет больше анкет.", reply_markup=main_reply_keyboard())
        await state.clear()
        await callback.answer()
        return
    await state.update_data(candidate_id=candidate.id)
    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "view_profile", Browse.candidate_id)
async def view_profile_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Нет анкеты.")
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Не найден.")
        return
    text = format_user_card(candidate) + "\n\nДополнительно:"
    markup = profile_actions_keyboard()
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "back_to_browse", Browse.candidate_id)
async def back_to_browse(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Ошибка.")
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Не найден.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    text = format_user_card(candidate)
    markup = browse_actions_keyboard()
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()