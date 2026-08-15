from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud

router = Router()

@router.callback_query(F.data == "chats")
async def chats_start(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Register first.")
        return
    chats = await crud.get_chats_for_user(session, user.id)
    if not chats:
        await callback.message.edit_text("No chats yet.")
        await callback.answer()
        return
    text = "💬 Your chats:\n\n"
    buttons = []
    for chat in chats:
        other_id = chat.user2_id if chat.user1_id == user.id else chat.user1_id
        other = await crud.get_user_by_id(session, other_id)
        if not other:
            continue
        name = other.name or other.username
        text += f"👤 {name}\n"
        buttons.append([InlineKeyboardButton(text=f"Chat with {name}", callback_data=f"openchat_{other.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("openchat_"))
async def open_chat_callback(callback: CallbackQuery):
    await callback.answer("Chat coming soon!", show_alert=True)