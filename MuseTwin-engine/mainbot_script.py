import os
import asyncio

from aiogram.utils import keyboard
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command , CommandStart
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("help"))
async def send_help(message: types.Message):
    commands = {
        "/start": "Welcome message",
        "/help": "Show this help",
        "/app": "Open the Mini App",
        "/premium": "Buy premium status",
    }
    help_text = "Available commands:\n" + "\n".join([f"{cmd} – {desc}" for cmd, desc in commands.items()])
    await message.answer(help_text)

@dp.message(Command("premium"))
async def premium(message: types.Message):
    await message.answer("Premium subscription – coming soon!")

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = [
        [types.KeyboardButton(
            text="Launch Mini App",
            web_app=WebAppInfo(url="#")
        )],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Choose an action"
    )
    await message.answer("Welcome! Click the button to launch the Mini App.",reply_markup=keyboard)

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    await message.answer(f"Data received: {message.web_app_data}")

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())