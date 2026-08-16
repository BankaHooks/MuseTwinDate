from typing import Union
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import Skip
from keyboards.inline import browse_actions_keyboard, report_reason_keyboard
from keyboards.reply import main_reply_keyboard
from states.browse import Browse
from states.like_message import LikeMessageState
from utils.helpers import format_user_card
from utils.matching import pick_candidate_simple
from utils.security import escape_markdown
import logging

logger = logging.getLogger(__name__)
router = Router()

async def show_candidate(event: Union[Message, CallbackQuery], state: FSMContext, session: AsyncSession):
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        target_message = event.message
    else:
        user_id = event.from_user.id
        target_message = event

    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await target_message.answer("Зарегистрируйтесь через /start")
        return

    candidate, score = await pick_candidate_simple(session, user)
    if not candidate:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать все анкеты", callback_data="show_all")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ])
        await target_message.answer("Нет больше новых анкет. Хотите посмотреть уже просмотренные?", reply_markup=markup)
        await state.clear()
        return

    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)

    data = await state.get_data()
    view_count = data.get("view_count", 0) + 1
    await state.update_data(view_count=view_count)

    if view_count % 7 == 0:
        try:
            await target_message.answer(
                "🔍 Вы просмотрели 7 анкет! Если заметили баг или есть идея, напишите @danhooks."
            )
        except:
            pass

    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    try:
        if candidate.photo_file_id:
            await target_message.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
        else:
            await target_message.answer(text, reply_markup=markup)
    except Exception as e:
        await target_message.answer(text, reply_markup=markup)

@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, session: AsyncSession):
    await show_candidate(message, state, session)

@router.callback_query(F.data == "browse")
async def browse_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await show_candidate(callback, state, session)
    await callback.answer()

@router.callback_query(F.data == "show_all")
async def show_all_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start", show_alert=True)
        return
    await session.execute(delete(Skip).where(Skip.user_id == user.id))
    await session.commit()
    await callback.message.delete()
    await show_candidate(callback, state, session)
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

    total_likes = await crud.get_likes_count(session, candidate.id)
    if total_likes > candidate.last_like_notification_count:
        count = total_likes
        display_count = "9+" if count > 9 else str(count)
        if count == 1:
            text = "Вас лайкнул 1 человек."
        elif 2 <= count <= 4:
            text = f"Вас лайкнули {display_count} человека."
        else:
            text = f"Вас лайкнули {display_count} человек."
        try:
            await callback.bot.send_message(candidate.telegram_id, text)
            candidate.last_like_notification_count = count
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to send like count notification: {e}")

    if like.is_mutual:
        safe_user_name = escape_markdown(user.name or user.username)
        safe_candidate_name = escape_markdown(candidate.name or candidate.username)
        user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
        candidate_link = f"@{candidate.username}" if candidate.username else f"[профиль](tg://user?id={candidate.telegram_id})"
        try:
            await callback.bot.send_message(
                candidate.telegram_id,
                f"💞 Взаимный лайк! Вы и **{safe_user_name}** понравились друг другу.\n"
                f"Напишите ему: {user_link}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mutual like to candidate failed: {e}")
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"💞 Взаимный лайк! Вы и **{safe_candidate_name}** понравились друг другу.\n"
                f"Напишите ему: {candidate_link}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mutual like to user failed: {e}")
        await callback.answer("Это взаимно! 💞")
    else:
        await callback.answer("Лайк поставлен!")

    await state.update_data(candidate_id=None)
    await show_next(callback, state, session)

@router.callback_query(F.data == "skip", Browse.candidate_id)
async def skip_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if candidate_id:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        await crud.create_skip(session, user.id, candidate_id)
    await state.update_data(candidate_id=None)
    await show_next(callback, state, session)

@router.callback_query(F.data == "send_envelope", Browse.candidate_id)
async def send_envelope_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Нет анкеты.")
        return
    await state.update_data(like_target=candidate_id)
    await state.set_state(LikeMessageState.text)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_envelope")]
    ])
    if callback.message.photo:
        await callback.message.edit_caption(
            caption="✉️ Введите текст сообщения, которое будет отправлено вместе с лайком.\n\nНапишите сообщение или нажмите «Отмена».",
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(
            text="✉️ Введите текст сообщения, которое будет отправлено вместе с лайком.\n\nНапишите сообщение или нажмите «Отмена».",
            reply_markup=markup
        )
    await callback.answer()

@router.callback_query(F.data == "cancel_envelope")
async def cancel_envelope(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await callback.message.delete()
    await show_candidate(callback, state, session)
    await callback.answer()

@router.message(LikeMessageState.text)
async def send_envelope_text(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    target_id = data.get("like_target")
    if not target_id:
        await message.answer("Ошибка.")
        await state.clear()
        return
    target = await crud.get_user_by_id(session, target_id)
    if not target:
        await message.answer("Пользователь не найден.")
        await state.clear()
        return
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not await crud.can_like(session, user):
        await message.answer("Вы исчерпали лимит лайков на сегодня (30). Купите премиум!")
        await state.clear()
        return
    like = await crud.create_like(session, user.id, target.id)
    await crud.increment_likes(session, user)
    text = message.text
    try:
        await message.bot.send_message(
            target.telegram_id,
            f"💌 Вас лайкнул пользователь {user.name or user.username} с сообщением:\n\n{text}"
        )
        await message.answer(f"Лайк отправлен! Сообщение: {text}")
    except Exception as e:
        await message.answer("Не удалось отправить сообщение.")
    if like.is_mutual:
        pass
    await state.clear()
    await show_next_from_message(message, state, session)

async def show_next_from_message(message: Message, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    candidate, score = await pick_candidate_simple(session, user)
    if not candidate:
        await message.answer("Нет больше новых анкет. Хотите посмотреть уже просмотренные?", reply_markup=main_reply_keyboard())
        await state.clear()
        return
    await state.update_data(candidate_id=candidate.id)
    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    try:
        if candidate.photo_file_id:
            await message.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
        else:
            await message.answer(text, reply_markup=markup)
    except Exception as e:
        await message.answer(text, reply_markup=markup)

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

@router.callback_query(F.data.startswith("reportreason_"), Browse.candidate_id)
async def report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    reason = callback.data.split("_", 1)[1]
    allowed = ["spam", "inappropriate", "fake", "other"]
    if reason not in allowed:
        await callback.answer("Некорректная причина.", show_alert=True)
        return
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
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать все анкеты", callback_data="show_all")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text("Нет больше новых анкет. Хотите посмотреть уже просмотренные?", reply_markup=markup)
        await state.clear()
        await callback.answer()
        return
    await state.update_data(candidate_id=candidate.id)

    data = await state.get_data()
    view_count = data.get("view_count", 0) + 1
    await state.update_data(view_count=view_count)

    if view_count % 7 == 0:
        try:
            await callback.message.answer(
                "🔍 Вы просмотрели 7 анкет! Если заметили баг или есть идея, напишите @danhooks."
            )
        except:
            pass

    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    try:
        if candidate.photo_file_id:
            await callback.message.edit_media(
                InputMediaPhoto(media=candidate.photo_file_id, caption=text),
                reply_markup=markup
            )
        else:
            await callback.message.edit_text(text, reply_markup=markup)
    except Exception as e:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()