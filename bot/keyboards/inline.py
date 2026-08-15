from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import config
import re

INTEREST_CATEGORIES = {
    "Активный отдых": [
        "Скалолазание", "Бег", "Плавание", "Йога", "Командные виды спорта",
        "Зимние виды спорта", "Фитнес", "Танцы", "Велопрогулки"
    ],
    "Искусство": [
        "Живопись", "Фотография", "Игра на музыкальных инструментах",
        "Каллиграфия", "Гончарное дело", "Театр", "Литература", "Граффити"
    ],
    "Музыка": [
        "Пение", "Сочинение музыки", "Посещение концертов",
        "Караоке", "Коллекционирование винила"
    ],
    "Кино": [
        "Сериаломания", "Документальное кино", "Фестивальное кино",
        "Киносъемка на телефон", "Киноблогинг"
    ],
    "Экстрим": [
        "Парапланеризм", "Кайтсерфинг", "Скейтбординг",
        "Банджи-джампинг", "Горный велосипед"
    ],
    "Рукоделие": [
        "Скрапбукинг", "Мозаика", "Шитьё", "Макраме", "Деревообработка"
    ],
    "Интеллект": [
        "Книги", "Настольные игры", "Астрономия", "История",
        "Научные подкасты", "Шахматы", "Психология", "Языки",
        "Судоку", "Кроссворды", "Дебаты", "Философия", "Научпоп-блог"
    ],
    "Природа": [
        "Собаководство", "Бёрдвотчинг", "Садоводство",
        "Волонтёрство в приютах", "Изучение дикой природы"
    ],
    "Гастрономия": [
        "Кофе-культура", "Виноделие", "Кулинария",
        "Гастрономический туризм", "Веганство", "Завтраки",
        "Фермерские продукты", "Коктейли", "Ферментация",
        "Дегустация сыров", "Кондитерское искусство", "Смузи"
    ],
    "Путешествия": [
        "Трекинг", "Автостоп", "Экотуризм", "Кемпинг",
        "Изучение городов", "Фестивальная культура"
    ],
    "Технологии": [
        "Видеоигры", "Кино", "Аниме", "Подкасты", "Киберспорт",
        "Комиксы", "Автомобили", "Мотоциклы",
        "Квадрокоптеры", "Сборка ПК", "Умный дом"
    ],
    "Саморазвитие": [
        "Осознанные сновидения", "Тайм-менеджмент",
        "Арт-терапия", "Восточные учения", "Дневник благодарности"
    ],
    "Развлечения": [
        "Ночные клубы", "Квизы", "Пикники",
        "Настольный теннис", "Стендап"
    ],
    "Разное": [
        "DIY", "Комнатные растения", "Осознанность",
        "Медитация", "Ретро-техника", "Карты и география"
    ]
}

def _clean(text):
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text)
    return cleaned.replace(' ', '_')

def _restore(text):
    return text.replace('_', ' ')

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Поиск", callback_data="browse")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Лайки", callback_data="likes")],
        [InlineKeyboardButton(text="Купить премиум", callback_data="premium")],
        [InlineKeyboardButton(text="Mini-App", web_app={"url": config.MINI_APP_URL})],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_view_keyboard(user):
    city_toggle_text = "Искать в моём городе" if user.search_city_only else "Искать везде"
    buttons = [
        [InlineKeyboardButton(text="Имя", callback_data="edit_name"),
         InlineKeyboardButton(text="Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="Город", callback_data="edit_city")],
        [InlineKeyboardButton(text="Жанры", callback_data="edit_genres"),
         InlineKeyboardButton(text="Группы", callback_data="edit_bands")],
        [InlineKeyboardButton(text="Песни", callback_data="edit_songs"),
         InlineKeyboardButton(text="Цель", callback_data="edit_goal")],
        [InlineKeyboardButton(text="Интересы", callback_data="edit_interests"),
         InlineKeyboardButton(text="Био", callback_data="edit_bio")],
        [InlineKeyboardButton(text="Фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="Пол партнера", callback_data="edit_preferred_gender")],
        [InlineKeyboardButton(text=city_toggle_text, callback_data="toggle_city")],
        [InlineKeyboardButton(text="Заполнить заново", callback_data="reset_profile")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gender_choose_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Мужской", callback_data="gender_Мужской")],
        [InlineKeyboardButton(text="Женский", callback_data="gender_Женский")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def preferred_gender_keyboard():
    genders = [("Мужской", "Мужской"), ("Женский", "Женский"), ("Любой", "Любой")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"pref_gender_{value}")] for label, value in genders]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def genre_choose_keyboard():
    genres = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal", "Other"]
    buttons = [[InlineKeyboardButton(text=g, callback_data=f"genre_add_{g}")] for g in genres]
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="genres_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def goal_keyboard():
    goals = [("Флирт", "flirt"), ("Общение", "communication"), ("Дружба", "friendship"), ("Отношения", "relationship")]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"goal_{value}")] for label, value in goals]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def interest_category_keyboard():
    buttons = []
    for category in INTEREST_CATEGORIES.keys():
        buttons.append([InlineKeyboardButton(text=category, callback_data=f"cat_{_clean(category)}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="interests_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def interest_items_keyboard(category, selected):
    topics = INTEREST_CATEGORIES.get(category, [])
    buttons = []
    for topic in topics:
        check = "✅ " if topic in selected else ""
        clean_topic = _clean(topic)
        buttons.append([InlineKeyboardButton(text=f"{check}{topic}", callback_data=f"interest_{clean_topic}")])
    buttons.append([InlineKeyboardButton(text="Назад к категориям", callback_data="interests_back")])
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

def likes_action_keyboard(user_id):
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