from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import main_menu_keyboard

router = Router()

@router.message(Command("menu"))
async def menu_command(message: Message):
    await message.answer("Main menu:", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text("Main menu:", reply_markup=main_menu_keyboard())
    await callback.answer()