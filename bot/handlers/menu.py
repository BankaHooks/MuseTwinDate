from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
from utils.helpers import send_security_notice_if_needed
from handlers.profile import show_profile_for_message
from handlers.likes import show_likes_for_message
from handlers.premium import show_premium_for_message
from handlers.browse import search_command

router = Router()

@router.message(Command("menu"))
async def menu_command(message: Message, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, зарегистрируйтесь через /start")
        return
    await message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await send_security_notice_if_needed(message, user, session)

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.message.answer("Пожалуйста, зарегистрируйтесь через /start")
        await callback.answer()
        return
    await callback.message.delete()
    await callback.message.answer("Главное меню:", reply_markup=main_reply_keyboard())
    await send_security_notice_if_needed(callback.message, user, session)
    await callback.answer()

@router.message(F.text == "Поиск")
async def search_button_handler(message: Message, state: FSMContext, session: AsyncSession):
    await search_command(message, state, session)

@router.message(F.text == "Профиль")
async def profile_button_handler(message: Message, session: AsyncSession):
    await show_profile_for_message(message, session)

@router.message(F.text == "Лайки")
async def likes_button_handler(message: Message, state: FSMContext, session: AsyncSession):
    await show_likes_for_message(message, state, session)

@router.message(F.text == "Купить премиум")
async def premium_button_handler(message: Message, session: AsyncSession):
    await show_premium_for_message(message, session)

@router.message(F.text == "Премиум-функции")
async def premium_features_button_handler(message: Message, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Зарегистрируйтесь через /start")
        return
    if not user.is_premium:
        await message.answer(
            "⚡ Эта функция доступна только с премиум-подпиской!\n"
            "Купите премиум в разделе «Купить премиум»."
        )
        return
    from keyboards.inline import premium_features_keyboard
    await message.answer("Доступные премиум-функции:", reply_markup=premium_features_keyboard())