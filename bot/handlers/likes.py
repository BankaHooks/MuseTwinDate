from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud

router = Router()
PAGE_SIZE = 5

@router.callback_query(F.data == "likes")
async def likes_start(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Register first.")
        return
    likes = await crud.get_likes_received(session, user.id)
    if not likes:
        await callback.message.edit_text("No likes yet.")
        await callback.answer()
        return
    # Store in state or just paginate using callback data
    await show_likes_page(callback, session, user.id, 0, likes)

async def show_likes_page(callback: CallbackQuery, session: AsyncSession, user_id: int, page: int, all_likes=None):
    if all_likes is None:
        likes = await crud.get_likes_received(session, user_id)
    else:
        likes = all_likes
    total = len(likes)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    if start >= total:
        await callback.answer("No more likes.")
        return
    page_likes = likes[start:end]
    text = "❤️ Your likes:\n\n"
    buttons = []
    for like in page_likes:
        from_user = like.from_user
        mutual = like.is_mutual
        line = f"👤 {from_user.name or from_user.username}, {from_user.age or '?'}, {from_user.city or ''}"
        if mutual:
            line += " ✅ mutual"
            btn = InlineKeyboardButton(text="💬 Chat", callback_data=f"chat_{from_user.id}")
        else:
            btn = InlineKeyboardButton(text="❤️ Like Back", callback_data=f"likeback_{from_user.id}")
        text += line + "\n"
        buttons.append([btn])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"likes_page_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"likes_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("likes_page_"))
async def likes_page_callback(callback: CallbackQuery, session: AsyncSession):
    page = int(callback.data.split("_")[2])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    likes = await crud.get_likes_received(session, user.id)
    await show_likes_page(callback, session, user.id, page, likes)

@router.callback_query(F.data.startswith("likeback_"))
async def like_back_callback(callback: CallbackQuery, session: AsyncSession):
    target_id = int(callback.data.split("_")[1])
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    like = await crud.create_like(session, user.id, target_id)
    if like.is_mutual:
        target = await crud.get_user_by_id(session, target_id)
        await callback.bot.send_message(target.telegram_id,
            f"🎉 Mutual! You and {user.name or user.username} liked each other.")
        await callback.answer("It's a match! 🎉")
    else:
        await callback.answer("Liked back!")
    # refresh likes list
    await likes_start(callback, session)