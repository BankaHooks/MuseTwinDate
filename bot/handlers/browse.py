from typing import Union
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import browse_actions_keyboard, report_reason_keyboard, profile_actions_keyboard, main_menu_keyboard
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
    candidate, score = await pick_candidate(session, user)
    if not candidate:
        await event.answer("Нет больше анкет для показа.")
        return
    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)
    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard(user.is_premium)
    if candidate.photo_file_id:
        await event.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=markup)
    else:
        await event.answer(text, reply_markup=markup)


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, session: AsyncSession):
    await show_candidate(message, state, session)


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
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Анкета не найдена.")
        await state.clear()
        return
    like = await crud.create_like(session, user.id, candidate.id)
    if like.is_mutual:
        await callback.bot.send_message(
            candidate.telegram_id,
            f"🎉 Взаимность! Вы и {user.name or user.username} понравились друг другу."
        )
        await callback.answer("Это взаимно! 🎉")
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
    await callback.message.edit_caption(
        caption="Выберите причину жалобы:",
        reply_markup=report_reason_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reportreason_"), Browse.candidate_id)
async def report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    reason = callback.data.split("_", 1)[1]
    data = await state.get_data()
    target_id = data.get("report_target")
    if not target_id:
        await callback.answer("Ошибка.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.create_report(session, user.id, target_id, reason)
    await callback.answer("Жалоба отправлена. Спасибо.", show_alert=True)
    await state.update_data(report_target=None)
    await show_next(callback, state, session)


@router.callback_query(F.data == "write_message", Browse.candidate_id)
async def write_message(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("Нет анкеты.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user.is_premium:
        await callback.answer("Эта функция доступна только с премиум-подпиской!", show_alert=True)
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    await callback.bot.send_message(
        candidate.telegram_id,
        f"Пользователь {user.name or user.username} хочет написать вам. Напишите ему в ответ."
    )
    await callback.answer("Сообщение отправлено!")


async def show_next(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    candidate, score = await pick_candidate(session, user)
    if not candidate:
        await callback.message.edit_text("Нет больше анкет.", reply_markup=main_menu_keyboard())
        await state.clear()
        await callback.answer()
        return
    await state.update_data(candidate_id=candidate.id)
    text = format_user_card(candidate, score)
    markup = browse_actions_keyboard(user.is_premium)
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
    text = format_user_card(candidate) + "\n\n🛡️ Дополнительно:"
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
    markup = browse_actions_keyboard(user.is_premium)
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()
