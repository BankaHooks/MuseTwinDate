from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from config import config

router = Router()

@router.message(Command("admin"))
async def admin_command(message: Message, session: AsyncSession):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("Unauthorized.")
        return
    reports = await crud.get_reports(session, resolved=False)
    if not reports:
        await message.answer("No pending reports.")
        return
    text = "📋 Pending reports:\n\n"
    for r in reports:
        reporter = await crud.get_user_by_id(session, r.reporter_id)
        reported = await crud.get_user_by_id(session, r.reported_id)
        text += f"ID {r.id}: {reporter.name or reporter.username} → {reported.name or reported.username}\n"
        text += f"Reason: {r.reason}\n\n"
    await message.answer(text)