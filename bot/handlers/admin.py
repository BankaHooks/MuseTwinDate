from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from database import crud
from database.models import User
from config import config
from utils.helpers import format_user_card

router = Router()
ADMIN_IDS = config.ADMIN_IDS

def admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Отправить уведомление", callback_data="admin_notify")],
        [InlineKeyboardButton(text="Выдать премиум", callback_data="admin_premium")],
        [InlineKeyboardButton(text="Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="Просмотр репортов", callback_data="admin_reports")],
        [InlineKeyboardButton(text="Закрыть", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("admin"))
async def admin_start(message: Message, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return
    await message.answer("Админ-панель:", reply_markup=admin_keyboard())

@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "admin_reports")
async def admin_reports(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    reports = await crud.get_reports(session, resolved=False)
    if not reports:
        await callback.message.edit_text("Нет непросмотренных репортов.", reply_markup=admin_keyboard())
        await callback.answer()
        return
    text = "📋 Непросмотренные репорты:\n\n"
    buttons = []
    for r in reports[:10]:
        reporter = await crud.get_user_by_id(session, r.reporter_id)
        reported = await crud.get_user_by_id(session, r.reported_id)
        reason_ru = {
            "spam": "Спам",
            "inappropriate": "Неприемлемый контент",
            "fake": "Фейковый профиль",
            "other": "Другое"
        }.get(r.reason, r.reason)
        text += f"ID {r.id}: {reporter.name or reporter.username} → {reported.name or reported.username}\n"
        text += f"Причина: {reason_ru}\n"
        if r.description:
            text += f"Описание: {r.description}\n"
        text += "\n"
        buttons.append([InlineKeyboardButton(
            text=f"👤 Анкета (ID {reported.id})",
            callback_data=f"admin_user_detail_{reported.id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    total = await session.scalar(select(func.count()).select_from(User))
    male = await session.scalar(select(func.count()).select_from(User).where(User.gender == "Мужской"))
    female = await session.scalar(select(func.count()).select_from(User).where(User.gender == "Женский"))
    active = await session.scalar(
        select(func.count()).select_from(User).where(User.last_activity >= datetime.utcnow() - timedelta(days=7))
    )
    premium = await session.scalar(select(func.count()).select_from(User).where(User.is_premium == True))
    text = f"📊 Статистика:\nВсего: {total}\nМужчин: {male}\nЖенщин: {female}\nАктивных (7 дней): {active}\nПремиум: {premium}"
    buttons = [
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users_list_all_0")],
        [InlineKeyboardButton(text="👨 Мужчины", callback_data="admin_users_list_male_0")],
        [InlineKeyboardButton(text="👩 Женщины", callback_data="admin_users_list_female_0")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_users_list_"))
async def admin_users_list(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    _, gender, page_str = callback.data.split("_")
    page = int(page_str)
    limit = 10
    offset = page * limit
    stmt = select(User).order_by(User.id)
    if gender == "male":
        stmt = stmt.where(User.gender == "Мужской")
    elif gender == "female":
        stmt = stmt.where(User.gender == "Женский")
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    users = await session.execute(stmt.offset(offset).limit(limit))
    users = users.scalars().all()
    if not users:
        await callback.answer("Нет пользователей.")
        return
    text = f"👥 Список пользователей ({(page*limit)+1}–{min((page+1)*limit, total)} из {total}):\n\n"
    buttons = []
    for u in users:
        name = u.name or u.username or "Без имени"
        text += f"ID {u.id}: {name} ({(u.username) and '@'+u.username or 'нет юза'})\n"
        buttons.append([InlineKeyboardButton(
            text=f"👤 {name}",
            callback_data=f"admin_user_detail_{u.id}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users_list_{gender}_{page-1}"))
    if (page+1)*limit < total:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin_users_list_{gender}_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Назад к статистике", callback_data="admin_users")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_detail_"))
async def admin_user_detail(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    user_id = int(callback.data.split("_")[3])
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        await callback.answer("Пользователь не найден.")
        return
    text = format_user_card(user)
    if user.username:
        profile_link = f"https://t.me/{user.username}"
    else:
        profile_link = f"tg://user?id={user.telegram_id}"
    buttons = [
        [InlineKeyboardButton(text="💬 Перейти в Telegram", url=profile_link)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    if user.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=user.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    await callback.message.delete()
    await callback.message.answer("Админ-панель:", reply_markup=admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_notify")
async def admin_notify_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    await state.set_state("admin_notify_text")
    await callback.message.edit_text("Введите текст уведомления (или отправьте /cancel для отмены):")
    await callback.answer()

@router.message(F.text, StateFilter("admin_notify_text"))
async def admin_notify_text(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет прав")
        return
    text = message.text
    await state.update_data(notify_text=text)
    await state.set_state("admin_notify_confirm")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить всем", callback_data="admin_send_all")],
        [InlineKeyboardButton(text="Отправить активным (7 дней)", callback_data="admin_send_active")],
        [InlineKeyboardButton(text="Отмена", callback_data="admin_close")]
    ])
    await message.answer(f"Подтвердите рассылку:\n\n{text}", reply_markup=kb)
    await state.clear()

@router.callback_query(F.data.startswith("admin_send_"))
async def admin_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    data = await state.get_data()
    text = data.get("notify_text")
    if not text:
        await callback.answer("Нет текста для отправки")
        return
    target = callback.data.split("_")[2]
    stmt = select(User)
    if target == "active":
        cutoff = datetime.utcnow() - timedelta(days=7)
        stmt = stmt.where(User.last_activity >= cutoff)
    users = await session.execute(stmt)
    users = users.scalars().all()
    count = 0
    for user in users:
        try:
            await callback.bot.send_message(user.telegram_id, text)
            count += 1
        except:
            pass
    await callback.message.edit_text(f"Уведомление отправлено {count} пользователям.")
    await callback.answer()
    await state.clear()

@router.callback_query(F.data == "admin_premium")
async def admin_premium_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    await state.set_state("admin_premium_id")
    await callback.message.edit_text("Введите Telegram ID пользователя (или username без @) и срок в месяцах (1, 3, 6) через пробел.\nПример: 123456789 3")
    await callback.answer()

@router.message(F.text, StateFilter("admin_premium_id"))
async def admin_premium_set(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет прав")
        return
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("Введите ID и срок через пробел (например: 123456789 3)")
        return
    identifier, months_str = parts[0], parts[1]
    if not months_str.isdigit():
        await message.answer("Срок должен быть числом (1, 3, 6).")
        return
    months = int(months_str)
    if months not in [1,3,6]:
        await message.answer("Допустимые сроки: 1, 3, 6 месяцев.")
        return
    try:
        if identifier.isdigit():
            user = await crud.get_user_by_telegram_id(session, int(identifier))
        else:
            user = await session.execute(select(User).where(User.username == identifier))
            user = user.scalar_one_or_none()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return
    if not user:
        await message.answer("Пользователь не найден.")
        return
    await crud.set_premium(session, user.id, months)
    await message.answer(f"Премиум выдан пользователю {user.name or user.username} на {months} месяцев.")
    await state.clear()

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")