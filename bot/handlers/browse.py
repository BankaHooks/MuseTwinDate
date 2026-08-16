from typing import Union
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import Skip
from keyboards.inline import browse_actions_keyboard, report_reason_keyboard, profile_actions_keyboard
from keyboards.reply import main_reply_keyboard
from states.browse import Browse
from states.report import ReportState
from utils.helpers import format_user_card
from utils.matching import pick_candidate_simple
from utils.security import escape_markdown

router = Router()

async def show_candidate(event: Union[Message, CallbackQuery], state: FSMContext, session: AsyncSession, reset_skips: bool = False):
    user_id = event.from_user.id
    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await event.answer("Зарегистрируйтесь через /start")
        return

    if reset_skips:
        await session.execute(delete(Skip).where(Skip.user_id == user.id))
        await session.commit()

    candidate, score = await pick_candidate_simple(session, user)
    if not candidate:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать все анкеты", callback_data="show_all")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ])
        await event.answer("Нет больше новых анкет. Хотите посмотреть уже просмотренные?", reply_markup=markup)
        return

    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)

    data = await state.get_data()
    view_count = data.get("view_count", 0) + 1
    await state.update_data(view_count=view_count)

    if view_count % 7 == 0:
        try:
            await event.answer(
                "🔍 Вы просмотрели 7 анкет! Если заметили баг или есть идея, напишите @danhooks."
            )
        except:
            pass

    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard()
    try:
        if candidate.photo_file_id:
            await event.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
        else:
            await event.answer(text, reply_markup=markup)
    except Exception as e:
        await event.answer(text, reply_markup=markup)

@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, session: AsyncSession):
    await show_candidate(message, state, session)

@router.callback_query(F.data == "browse")
async def browse_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await show_candidate(callback.message, state, session)
    await callback.answer()

@router.callback_query(F.data == "show_all")
async def show_all_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await show_candidate(callback.message, state, session, reset_skips=True)
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
        except:
            pass

    if like.is_mutual:
        safe_user_name = escape_markdown(user.name or user.username)
        safe_candidate_name = escape_markdown(candidate.name or candidate.username)
        user_link = f"@{user.username}" if user.username else f"[профиль](tg://user?id={user.telegram_id})"
        candidate_link = f"@{candidate.username}" if candidate.username else f"[профиль](tg://user?id={candidate.telegram_id})"
        try:
            await callback.bot.send_message(
                candidate.telegram_id,
                f"Взаимный лайк! Вы и {safe_user_name} понравились друг другу.\n"
                f"Напишите ему: {user_link}",
                parse_mode="Markdown"
            )
        except:
            pass
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"Взаимный лайк! Вы и {safe_candidate_name} понравились друг другу.\n"
                f"Напишите ему: {candidate_link}",
                parse_mode="Markdown"
            )
        except:
            pass
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

@router.callback_query(F.data.startswith("reportreason_"), Browse.candidate_id)
async def report_reason(callback: CallbackQuery, state: FSMContext):
    reason = callback.data.split("_", 1)[1]
    allowed = ["spam", "inappropriate", "fake", "other"]
    if reason not in allowed:
        await callback.answer("Некорректная причина.", show_alert=True)
        return
    await state.update_data(report_reason=reason)
    await state.set_state(ReportState.description)
    await callback.message.edit_text(
        "Опишите проблему подробнее (или отправьте 'Пропустить', чтобы оставить пустым):"
    )
    await callback.answer()

@router.message(ReportState.description)
async def report_description(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    target_id = data.get("report_target")
    reason = data.get("report_reason")
    if not target_id or not reason:
        await message.answer("Ошибка: не найдена цель или причина.")
        await state.clear()
        return
    description = message.text if message.text.lower() != "пропустить" else None
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    await crud.create_report(session, user.id, target_id, reason, description)
    await message.answer("Жалоба отправлена. Спасибо!", reply_markup=main_reply_keyboard())
    await state.clear()

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