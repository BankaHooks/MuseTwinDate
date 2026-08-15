from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud

router = Router()


@router.callback_query(F.data == "chats")
async def chats_start(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    chats = await crud.get_chats_for_user(session, user.id)
    if not chats:
        await callback.message.edit_text(
            "У вас пока нет чатов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    text = "💬 Ваши чаты:\n\n"
    buttons = []
    for chat in chats:
        other_id = chat.user2_id if chat.user1_id == user.id else chat.user1_id
        other = await crud.get_user_by_id(session, other_id)
        if not other:
            continue
        name = other.name or other.username or "Пользователь"
        buttons.append([InlineKeyboardButton(text=f"Чат с {name}", callback_data=f"openchat_{other.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("openchat_"))
async def open_chat_callback(callback: CallbackQuery):
    await callback.answer("Функция чата скоро появится!", show_alert=True)
