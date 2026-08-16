from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import config

def _clean(text):
    if not text:
        return ""
    return text.replace(' ', '_')

def _restore(text):
    if not text:
        return ""
    return text.replace('_', ' ')

INTEREST_CATEGORIES = {
    "Спорт": [
        "Бег", "Йога", "Плавание", "Велопрогулки", "Фитнес",
        "Командные игры", "Танцы", "Лыжи", "Пешие прогулки", "Настольный теннис"
    ],
    "Кулинария": [
        "Готовка", "Выпечка", "Кофе", "Рестораны", "Барбекю",
        "Здоровое питание", "Виноделие", "Крафтовое пиво", "Азиатская кухня", "Завтраки"
    ],
    "Кино": [
        "Кино", "Сериалы", "Документальное кино", "Мультфильмы", "Походы в кино",
        "Домашние киновечера", "Фестивальное кино", "Рецензии", "Старые фильмы", "Треш-кино"
    ],
    "Книги": [
        "Художественная литература", "Нон-фикшн", "Фантастика", "Детективы",
        "Саморазвитие", "Чтение перед сном", "Книжные клубы", "Биографии",
        "Научпоп", "Поэзия"
    ],
    "Путешествия": [
        "Автопутешествия", "Пляжный отдых", "Горные походы", "Экскурсии",
        "Кемпинг", "Речные круизы", "Фотоохота", "Национальные парки",
        "Зарубежные поездки", "Спонтанные вылазки"
    ],
    "Интеллект": [
        "Настольные игры", "Шахматы", "Изучение языков", "Подкасты",
        "История", "Астрономия", "Психология", "Дебаты", "Головоломки", "Лекции"
    ],
    "Творчество": [
        "Рисование", "Фотография", "Игра на инструменте", "Караоке",
        "Гончарство", "Шитьё", "Декор", "Интерьерный дизайн", "Флористика", "Скрапбукинг"
    ],
    "Техника": [
        "Автомобили", "Мотоциклы", "Гаджеты", "Сборка ПК",
        "Фото-оборудование", "Квадрокоптеры", "Электротранспорт",
        "Робототехника", "Игровые приставки", "VR/AR"
    ],
    "Развлечения": [
        "Караоке-бары", "Квизы", "Стендап", "Пикники",
        "Ночная жизнь", "Дружеские посиделки", "Фестивали",
        "Дайвинг", "Боулинг", "Музеи"
    ],
    "Образ жизни": [
        "Медитация", "Осознанное потребление", "Волонтёрство",
        "Дневник благодарности", "Сон и режим", "Психоподдержка",
        "Прогулки", "Спорттрансляции", "Тайм-менеджмент", "Уход за собой"
    ]
}

GAMES_CATEGORIES = {
    "Кооперативные": [
        "R.E.P.O.", "Helldivers 2", "It Takes Two", "Split Fiction", "Risk of Rain 2",
        "Deep Rock Galactic", "Payday 3", "GTFO", "Barotrauma", "Ready or Not"
    ],
    "Шутеры": [
        "Counter-Strike 2", "VALORANT", "Apex Legends", "Fortnite", "Call of Duty: Black Ops 6",
        "Rainbow Six: Siege X", "Marathon", "DOOM: The Dark Ages", "Pragmata", "THE FINALS",
        "PUBG", "Overwatch 2", "Destiny 2", "Warframe", "Escape from Tarkov", "Hunt: Showdown"
    ],
    "Выживания": [
        "Subnautica 2", "ARK: Survival Ascended", "Minecraft", "Don't Starve Together", "Rust",
        "DayZ", "The Forest", "Sons of the Forest", "Grounded", "Valheim", "Project Zomboid", "7 Days to Die"
    ],
    "Стратегии": [
        "Warhammer 40,000: Dawn of War IV", "Heroes of Might and Magic: Olden Era",
        "Civilization VII", "Total War: Warhammer 3", "Age of Empires IV", "Iron Harvest",
        "Company of Heroes 3", "Northgard", "Dune: Spice Wars", "Menace"
    ],
    "MOBA / Геройские": [
        "Dota 2", "League of Legends", "Mobile Legends: Bang Bang", "Marvel Rivals", "Smite 2"
    ],
    "MMORPG / RPG": [
        "World of Warcraft", "Final Fantasy XIV", "Genshin Impact", "Path of Exile 2",
        "Diablo IV: Lord of Hatred", "The Blood of Dawnwalker", "Kingdom Come: Deliverance 2",
        "Baldur's Gate 3", "Clair Obscur: Expedition 33", "Elden Ring Nightreign",
        "Cyberpunk 2077", "Resident Evil Requiem", "Silent Hill f", "Death Stranding 2: On the Beach"
    ]
}

def welcome_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Начать регистрацию", callback_data="welcome_start")],
        [InlineKeyboardButton(text="Написать в ЛС @danhooks", url="https://t.me/danhooks")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Поиск", callback_data="browse")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Лайки", callback_data="likes")],
        [InlineKeyboardButton(text="Купить премиум", callback_data="premium")],
        [InlineKeyboardButton(text="Mini-App", web_app={"url": config.MINI_APP_URL})],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Редактировать профиль", callback_data="profile_edit_menu")],
        [InlineKeyboardButton(text="Параметры поиска", callback_data="profile_search_settings")],
        [InlineKeyboardButton(text="🔗 Пригласить друзей", callback_data="show_referral")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_edit_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Имя", callback_data="edit_name"),
         InlineKeyboardButton(text="Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="Город", callback_data="edit_city")],
        [InlineKeyboardButton(text="Жанры", callback_data="edit_genres"),
         InlineKeyboardButton(text="Группы", callback_data="edit_bands")],
        [InlineKeyboardButton(text="Песни", callback_data="edit_songs"),
         InlineKeyboardButton(text="Цель", callback_data="edit_goal")],
        [InlineKeyboardButton(text="Интересы", callback_data="edit_interests"),
         InlineKeyboardButton(text="Игры", callback_data="edit_games")],
        [InlineKeyboardButton(text="Био", callback_data="edit_bio"),
         InlineKeyboardButton(text="Фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="Обновить рекомендации", callback_data="refresh_recommendations")],
        [InlineKeyboardButton(text="Перезаполнить анкету заново", callback_data="reset_profile")],
        [InlineKeyboardButton(text="Назад", callback_data="profile_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_search_settings_keyboard(user):
    city_toggle_text = "Искать в моём городе" if user.search_city_only else "Искать везде"
    hide_text = "Скрыть анкету" if not user.is_hidden else "Показать анкету"
    buttons = [
        [InlineKeyboardButton(text="Пол партнера", callback_data="edit_preferred_gender")],
        [InlineKeyboardButton(text=city_toggle_text, callback_data="toggle_city")],
        [InlineKeyboardButton(text=hide_text, callback_data="toggle_hide")],
        [InlineKeyboardButton(text="Назад", callback_data="profile_back")]
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
    category = category.strip()
    topics = INTEREST_CATEGORIES.get(category, [])
    buttons = []
    for topic in topics:
        check = "✅ " if topic in selected else ""
        clean_topic = _clean(topic)
        buttons.append([InlineKeyboardButton(text=f"{check}{topic}", callback_data=f"interest_{clean_topic}")])
    buttons.append([InlineKeyboardButton(text="Назад к категориям", callback_data="interests_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def games_category_keyboard():
    buttons = []
    for category in GAMES_CATEGORIES.keys():
        buttons.append([InlineKeyboardButton(text=category, callback_data=f"gamecat_{_clean(category)}")])
    buttons.append([InlineKeyboardButton(text="Не играю", callback_data="games_none")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="games_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def games_items_keyboard(category, selected):
    category = category.strip()
    games = GAMES_CATEGORIES.get(category, [])
    buttons = []
    for game in games:
        check = "✅ " if game in selected else ""
        clean_game = _clean(game)
        buttons.append([InlineKeyboardButton(text=f"{check}{game}", callback_data=f"game_{clean_game}")])
    buttons.append([InlineKeyboardButton(text="Назад к категориям", callback_data="games_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def browse_actions_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Скип", callback_data="skip"),
         InlineKeyboardButton(text="Лайк", callback_data="like")],
        [InlineKeyboardButton(text="✉️ Конверт", callback_data="send_envelope"),
         InlineKeyboardButton(text="Профиль", callback_data="view_profile")],
        [InlineKeyboardButton(text="Пожаловаться", callback_data="report_user")],
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

def premium_payment_methods_keyboard():
    buttons = [
        [InlineKeyboardButton(text="⭐ Купить за звёзды", callback_data="premium_stars")],
        [InlineKeyboardButton(text="💳 Оплатить картой / СБП", callback_data="premium_card")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_stars_plans_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 месяц – 100 ⭐", callback_data="premium_stars_1")],
        [InlineKeyboardButton(text="3 месяца – 250 ⭐", callback_data="premium_stars_3")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="premium_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_rub_plans_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 месяц – 150 ₽", callback_data="premium_rub_1")],
        [InlineKeyboardButton(text="3 месяца – 350 ₽", callback_data="premium_rub_3")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="premium_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_features_keyboard():
    buttons = [
        [InlineKeyboardButton(text="AI-подбор пары", callback_data="ai_match")],
        [InlineKeyboardButton(text="Мой музыкальный профиль", callback_data="ai_music_profile")],
        [InlineKeyboardButton(text="Свидание вслепую", callback_data="blind_date")],
        [InlineKeyboardButton(text="🎮 Найти союзника в игру", callback_data="find_gaming_buddy")],
        [InlineKeyboardButton(text="Сбросить историю", callback_data="reset_history")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gaming_categories_keyboard():
    buttons = []
    for category in GAMES_CATEGORIES.keys():
        buttons.append([InlineKeyboardButton(text=category, callback_data=f"gaming_cat_{_clean(category)}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="premium_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def gaming_games_keyboard(category):
    category = category.strip()
    games = GAMES_CATEGORIES.get(category, [])
    buttons = []
    for game in games:
        clean_game = _clean(game)
        buttons.append([InlineKeyboardButton(text=game, callback_data=f"gaming_game_{clean_game}")])
    buttons.append([InlineKeyboardButton(text="🔙 К категориям", callback_data="gaming_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)