from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import browse_actions_keyboard, main_menu_keyboard, report_reason_keyboard
from utils.helpers import format_user_card
from states.browse import Browse

router = Router()

@router.callback_query(F.data == "browse")
async def browse_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Register with /start")
        return
    candidate = await crud.get_random_candidate(session, user.id)
    if not candidate:
        await callback.message.edit_text("No more users.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    await state.set_state(Browse.candidate_id)
    await state.update_data(candidate_id=candidate.id)
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=candidate.photo_file_id or "https://via.placeholder.com/150",
        caption=format_user_card(candidate),
        reply_markup=browse_actions_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "like", Browse.candidate_id)
async def like_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("No user.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("User not found.")
        await state.clear()
        return
    like = await crud.create_like(session, user.id, candidate.id)
    if like.is_mutual:
        await callback.bot.send_message(candidate.telegram_id,
            f"🎉 Mutual! You and {user.name or user.username} liked each other.")
        await callback.answer("It's a match! 🎉")
    else:
        await callback.answer("Liked!")
    await browse_next(callback, state, session)

@router.callback_query(F.data == "skip", Browse.candidate_id)
async def skip_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if candidate_id:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        await crud.create_skip(session, user.id, candidate_id)
    await browse_next(callback, state, session)

async def browse_next(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    candidate = await crud.get_random_candidate(session, user.id)
    if not candidate:
        await callback.message.edit_text("No more users.", reply_markup=main_menu_keyboard())
        await state.clear()
        await callback.answer()
        return
    await state.update_data(candidate_id=candidate.id)
    await callback.message.edit_media(
        InputMediaPhoto(media=candidate.photo_file_id or "https://via.placeholder.com/150",
                        caption=format_user_card(candidate)),
        reply_markup=browse_actions_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "view_profile", Browse.candidate_id)
async def view_profile_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("No user.")
        return
    candidate = await crud.get_user_by_id(session, candidate_id)
    if not candidate:
        await callback.answer("Not found.")
        return
    text = format_user_card(candidate) + "\n\n🛡️ Options:"
    await callback.message.edit_caption(
        caption=text,
        reply_markup=report_reason_keyboard()
    )
    await callback.answer()