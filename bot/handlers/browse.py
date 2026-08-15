from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import browse_actions_keyboard, report_reason_keyboard, main_menu_keyboard
from utils.helpers import format_user_card
from states.browse import Browse
from aiogram.filters import Command

router = Router()

@router.callback_query(F.data == "browse")  # если оставим кнопку "Поиск" – но у нас её нет в меню, но можем добавить позже
async def browse_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    # этот метод будет вызван, если мы добавим кнопку поиска, но пока в меню её нет, можно использовать как внутренний вызов
    pass

# Но поскольку в новом меню нет кнопки "Поиск", мы можем сделать, чтобы при входе в бота (после регистрации) сразу показывалась анкета? 
# Или добавим кнопку "Поиск" отдельно? Пользователь сказал: "В меню должны быть такие кнопки как: профиль, купить премиум, запустить mini-app, и лайки." – поиска нет в меню.
# Значит, поиск будет запускаться автоматически после регистрации или через какую-то другую команду? Может, он подразумевает, что при старте бота после регистрации будет показываться анкета? 
# Уточним. Но пока реализуем как отдельную команду /search или callback, чтобы было.

# Я добавлю обработчик для команды /search, а также в меню можно будет добавить кнопку, но по ТЗ её нет – возможно, "лайки" и "поиск" объединены? 
# В любом случае, предоставлю функционал, а ты потом прикрутишь.

@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, session: AsyncSession):
    await show_candidate(message, state, session)

async def show_candidate(event: Message or CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = event.from_user.id
    user = await crud.get_user_by_telegram_id(session, user_id)
    if not user:
        await event.answer("Зарегистрируйтесь через /start")
        return
    candidate = await crud.get_random_candidate(session, user.id)
    if not candidate:
        await event.answer("Нет больше анкет для показа.")
        return
    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)
    is_premium = user.is_premium
    text = format_user_card(candidate)
    if candidate.photo_file_id:
        await event.answer_photo(photo=candidate.photo_file_id, caption=text, reply_markup=browse_actions_keyboard(is_premium))
    else:
        await event.answer(text, reply_markup=browse_actions_keyboard(is_premium))

# Обработчики кнопок поиска
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
        await callback.bot.send_message(candidate.telegram_id,
            f"🎉 Взаимность! Вы и {user.name or user.username} понравились друг другу.")
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
    # Сохраним в состоянии, на кого жалуемся
    await state.update_data(report_target=candidate_id)
    await callback.message.edit_caption(
        caption="Выберите причину жалобы:",
        reply_markup=report_reason_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("report_"))
async def report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    reason = callback.data.split("_", 1)[1]
    data = await state.get_data()
    target_id = data.get("report_target")
    if not target_id:
        await callback.answer("Ошибка.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.create_report(session, user.id, target_id, reason)
    await callback.message.edit_text("Жалоба отправлена. Спасибо.")
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
    # Отправляем сообщение через бота (можно сделать inline-кнопку с переходом в ЛС)
    await callback.bot.send_message(candidate.telegram_id,
        f"Пользователь {user.name or user.username} хочет написать вам. Напишите ему в ответ.")
    await callback.answer("Сообщение отправлено!")

async def show_next(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    candidate = await crud.get_random_candidate(session, user.id)
    if not candidate:
        await callback.message.edit_text("Нет больше анкет.", reply_markup=main_menu_keyboard())
        await state.clear()
        await callback.answer()
        return
    await state.update_data(candidate_id=candidate.id)
    is_premium = user.is_premium
    text = format_user_card(candidate)
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=browse_actions_keyboard(is_premium)
        )
    else:
        await callback.message.edit_text(text, reply_markup=browse_actions_keyboard(is_premium))
    await callback.answer()

# Обработчик просмотра профиля из карточки
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
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к анкете", callback_data="back_to_browse")]
            ])
        )
    else:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к анкете", callback_data="back_to_browse")]
        ]))
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
    is_premium = user.is_premium
    text = format_user_card(candidate)
    if candidate.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=candidate.photo_file_id, caption=text),
            reply_markup=browse_actions_keyboard(is_premium)
        )
    else:
        await callback.message.edit_text(text, reply_markup=browse_actions_keyboard(is_premium))
    await callback.answer()