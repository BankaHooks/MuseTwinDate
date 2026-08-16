from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.horoscope import ZODIAC_SIGNS, get_daily_horoscope

router = Router()

def zodiac_keyboard():
    buttons = []
    row = []
    for i, sign in enumerate(ZODIAC_SIGNS):
        row.append(InlineKeyboardButton(text=sign, callback_data=f"zodiac_{sign}"))
        if len(row) == 3 or i == len(ZODIAC_SIGNS) - 1:
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("horoscope"))
async def horoscope_command(message: Message):
    await message.answer("Выберите ваш знак зодиака:", reply_markup=zodiac_keyboard())

@router.message(F.text == "Гороскоп")
async def horoscope_button_handler(message: Message):
    await horoscope_command(message)

@router.callback_query(F.data.startswith("zodiac_"))
async def zodiac_callback(callback: CallbackQuery):
    sign_ru = callback.data.split("_", 1)[1]
    await callback.message.edit_text("🔮 Запрашиваю гороскоп...")
    horoscope = await get_daily_horoscope(sign_ru)
    if horoscope:
        await callback.message.edit_text(horoscope)
    else:
        await callback.message.edit_text("Не удалось получить гороскоп. Попробуйте позже.")
    await callback.answer()