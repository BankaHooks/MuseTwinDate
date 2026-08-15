from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Поиск", callback_data="browse")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Лайки", callback_data="likes")],
        [InlineKeyboardButton(text="Купить премиум", callback_data="premium")],
        [InlineKeyboardButton(text="Mini-App", web_app={"url": "https://your-domain.com/MuseTwinDate/"})],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_view_keyboard(user):
    city_toggle_text = "Искать в моём городе" if user.search_city_only else "Искать везде"
    buttons = [
        [InlineKeyboardButton(text="Имя", callback_data="edit_name"),
         InlineKeyboardButton(text="Свой пол", callback_data="edit_gender")],
        [InlineKeyboardButton(text="Возраст", callback_data="edit_age"),
         InlineKeyboardButton(text="Город", callback_data="edit_city")],
        [InlineKeyboardButton(text="Жанр", callback_data="edit_genre"),
         InlineKeyboardButton(text="Группа", callback_data="edit_band")],
        [InlineKeyboardButton(text="Песни", callback_data="edit_songs"),
         InlineKeyboardButton(text="Био", callback_data="edit_bio")],
        [InlineKeyboardButton(text="Фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="Пол партнера", callback_data="edit_preferred_gender")],
        [InlineKeyboardButton(text=city_toggle_text, callback_data="toggle_city")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gender_choose_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Мужской", callback_data="gender_male")],
        [InlineKeyboardButton(text="Женский", callback_data="gender_female")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def preferred_gender_keyboard():
    genders = [("Мужской", "male"), ("Женский", "female"), ("Любой", "any")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"pref_gender_{value}")] for label, value in genders]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def genre_keyboard():
    genres = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal", "Other"]
    buttons = [[InlineKeyboardButton(text=g, callback_data=f"genre_{g}")] for g in genres]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gender_keyboard():
    genders = [("Мужской", "male"), ("Женский", "female"), ("Любой", "any")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"gender_{value}")] for label, value in genders]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def browse_actions_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Скип", callback_data="skip"),
         InlineKeyboardButton(text="Лайк", callback_data="like")],
        [InlineKeyboardButton(text="Профиль", callback_data="view_profile"),
         InlineKeyboardButton(text="Пожаловаться", callback_data="report_user")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_actions_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Назад к анкете", callback_data="back_to_browse")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def likes_action_keyboard(user_id: int):
    buttons = [
        [InlineKeyboardButton(text="Взаимно", callback_data=f"likeback_{user_id}")],
        [InlineKeyboardButton(text="Пропустить", callback_data=f"skip_like_{user_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="likes_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def report_reason_keyboard():
    reasons = [("Спам", "spam"), ("Неприемлемый контент", "inappropriate"), ("Фейковый профиль", "fake"), ("Другое", "other")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"reportreason_{value}")] for label, value in reasons]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_plans_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 месяц – 100 звезд", callback_data="premium_1")],
        [InlineKeyboardButton(text="3 месяца – 250 звезд", callback_data="premium_3")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)