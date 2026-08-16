from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from utils.security import escape_markdown

router = Router()

@router.callback_query(F.data == "show_referral")
async def show_referral(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    if not user.referral_code:
        user.referral_code = await crud.generate_referral_code(user.telegram_id)
        await session.commit()
    link = f"t.me/MuseTwin_bot?start={user.referral_code}"
    text = (
        f"🔗 Ваша реферальная ссылка:\n\n"
        f"`{link}`\n\n"
        "Приводите друзей и получайте скидку до 90% на премиум!\n"
        f"Приведено друзей: {user.referral_count}\n"
        f"Ваша скидка: {user.referral_discount}%"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_referral")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_back")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "copy_referral")
async def copy_referral(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user or not user.referral_code:
        await callback.answer("Ошибка")
        return
    link = f"t.me/MuseTwin_bot?start={user.referral_code}"
    try:
        await callback.bot.send_message(
            callback.from_user.id,
            f"Ваша ссылка для приглашения:\n\n`{link}`",
            parse_mode="Markdown"
        )
        await callback.answer("Ссылка отправлена в чат!")
    except Exception as e:
        await callback.answer("Не удалось отправить")