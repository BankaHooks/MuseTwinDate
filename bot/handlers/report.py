from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.inline import main_menu_keyboard, report_reason_keyboard
from states.browse import Browse

router = Router()

@router.callback_query(F.data.startswith("report_"))
async def report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    reason = callback.data.split("_", 1)[1]
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        await callback.answer("No user to report.")
        return
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    await crud.create_report(session, user.id, candidate_id, reason)
    await callback.message.edit_text("Report submitted. Thank you.", reply_markup=main_menu_keyboard())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def cancel_report(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Cancelled.", reply_markup=main_menu_keyboard())
    await callback.answer()