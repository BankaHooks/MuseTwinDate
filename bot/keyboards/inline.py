from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="browse")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="❤️ Лайки", callback_data="likes")],
        [InlineKeyboardButton(text="💬 Чаты", callback_data="chats")],
        [InlineKeyboardButton(text="⭐ Купить премиум", callback_data="premium")],
        [InlineKeyboardButton(text="🎵 Запустить Mini-App", web_app={"url": "https://your-domain.com/MuseTwinDate/"})],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_view_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✏️ Имя", callback_data="edit_name"),
         InlineKeyboardButton(text="✏️ Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="✏️ Город", callback_data="edit_city"),
         InlineKeyboardButton(text="✏️ Жанр", callback_data="edit_genre")],
        [InlineKeyboardButton(text="✏️ Группа", callback_data="edit_band"),
         InlineKeyboardButton(text="✏️ Пол партнера", callback_data="edit_gender")],
        [InlineKeyboardButton(text="✏️ Песни", callback_data="edit_songs"),
         InlineKeyboardButton(text="✏️ Био", callback_data="edit_bio")],
        [InlineKeyboardButton(text="🖼️ Фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def genre_keyboard():
    genres = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal", "Other"]
    buttons = [[InlineKeyboardButton(text=g, callback_data=f"genre_{g}")] for g in genres]
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gender_keyboard():
    genders = [("Мужской", "male"), ("Женский", "female"), ("Любой", "any")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"gender_{value}")] for label, value in genders]
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def browse_actions_keyboard(is_premium: bool = False):
    buttons = [
        [InlineKeyboardButton(text="⏩ Скип", callback_data="skip"),
         InlineKeyboardButton(text="❤️ Лайк", callback_data="like")],
    ]
    if is_premium:
        buttons.append([InlineKeyboardButton(text="💬 Написать в ЛС", callback_data="write_message")])
    buttons.append([InlineKeyboardButton(text="👤 Профиль", callback_data="view_profile"),
                     InlineKeyboardButton(text="🚫 Пожаловаться", callback_data="report_user")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_actions_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔙 Назад к анкете", callback_data="back_to_browse")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def likes_action_keyboard(user_id: int):
    buttons = [
        [InlineKeyboardButton(text="❤️ Взаимно", callback_data=f"likeback_{user_id}")],
        [InlineKeyboardButton(text="⏩ Пропустить", callback_data=f"skip_like_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="likes_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def report_reason_keyboard():
    reasons = [("Спам", "spam"), ("Неприемлемый контент", "inappropriate"), ("Фейковый профиль", "fake"), ("Другое", "other")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"reportreason_{value}")] for label, value in reasons]
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_plans_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 месяц – 100 ⭐", callback_data="premium_1")],
        [InlineKeyboardButton(text="3 месяца – 250 ⭐", callback_data="premium_3")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)