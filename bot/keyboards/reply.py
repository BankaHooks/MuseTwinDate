from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_reply_keyboard():
    buttons = [
        [
            KeyboardButton(text="Поиск"),
            KeyboardButton(text="Профиль"),
        ],
        [
            KeyboardButton(text="Лайки"),
            KeyboardButton(text="Купить премиум"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )