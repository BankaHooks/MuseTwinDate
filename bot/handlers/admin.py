from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from database import crud
from database.models import User
from config import config

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
        await callback.message.edit_text("Нет непросмотренных репортов.")
        await callback.answer()
        return
    text = "Непросмотренные репорты:\n\n"
    for r in reports[:10]:
        reporter = await crud.get_user_by_id(session, r.reporter_id)
        reported = await crud.get_user_by_id(session, r.reported_id)
        text += f"ID {r.id}: {reporter.name or reporter.username} → {reported.name or reported.username}\n"
        text += f"Причина: {r.reason}\n\n"
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    total = await session.scalar(select(func.count()).select_from(User))
    active = await session.scalar(
        select(func.count()).select_from(User).where(User.last_activity >= datetime.utcnow() - timedelta(days=7))
    )
    premium = await session.scalar(select(func.count()).select_from(User).where(User.is_premium == True))
    text = f"Всего пользователей: {total}\nАктивных за 7 дней: {active}\nПремиум: {premium}"
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
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