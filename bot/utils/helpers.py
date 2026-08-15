import random
from datetime import datetime, timedelta

SECURITY_TIPS = [
    "Никогда не переводите деньги незнакомым людям.",
    "Не делитесь личными данными (адрес, паспорт, телефон).",
    "Если просят фото с паспортом — мошенники.",
    "Не переходите по подозрительным ссылкам.",
    "Если собеседник просит деньги — заблокируйте.",
    "Не передавайте доступ к вашему Telegram.",
    "Не подтверждайте номера по SMS от незнакомцев.",
    "Включите двухфакторную аутентификацию в Telegram.",
]

CITY_SYNONYMS = {
    "москва": ["мск", "msk", "москва", "moscow"],
    "санкт-петербург": ["спб", "питер", "санкт-петербург", "spb", "piter", "saint petersburg"],
    "нижний новгород": ["нн", "нижний", "нижний новгород", "nnovgorod"],
    "екатеринбург": ["екб", "екатеринбург", "ekb", "yekaterinburg"],
    "казань": ["казань", "kazan", "кзн"],
    "новосибирск": ["новосибирск", "nsk", "новосиб"],
    "челябинск": ["челябинск", "chel"],
    "самара": ["самара", "samara"],
    "омск": ["омск", "omsk"],
    "ростов-на-дону": ["ростов", "ростов-на-дону", "rostov"],
    "уфа": ["уфа", "ufa"],
    "красноярск": ["красноярск", "krasnoyarsk"],
    "пермь": ["пермь", "perm"],
    "воронеж": ["воронеж", "voronezh"],
    "волгоград": ["волгоград", "volgograd"],
    "кемерово": ["кемерово", "kemerovo"],
    "томск": ["томск", "tomsk"],
    "иркутск": ["иркутск", "irkutsk"],
    "хабаровск": ["хабаровск", "khabarovsk"],
    "ярославль": ["ярославль", "yaroslavl"],
    "владивосток": ["владивосток", "vladivostok"],
    "сочи": ["сочи", "sochi"],
    "калининград": ["калининград", "kaliningrad"],
    "тверь": ["тверь", "tver"],
    "благовещенск": ["благовещенск", "blagoveshchensk"],
    "псков": ["псков", "pskov"],
    "смоленск": ["смоленск", "smolensk"],
    "рязань": ["рязань", "ryazan"],
    "липецк": ["липецк", "lipetsk"],
    "тула": ["тула", "tula"],
    "киров": ["киров", "kirov"],
    "ижевск": ["ижевск", "izhevsk"],
    "ульяновск": ["ульяновск", "ulyanovsk"],
    "махачкала": ["махачкала", "makhachkala"],
    "севастополь": ["севастополь", "sevastopol"],
    "симферополь": ["симферополь", "simferopol"],
    "донецк": ["донецк", "donetsk"],
    "луганск": ["луганск", "lugansk"],
    "горловка": ["горловка", "gorlovka"],
    "макеевка": ["макеевка", "makeevka"],
    "евпатория": ["евпатория", "evpatoria"],
    "ялта": ["ялта", "yalta"],
    "судак": ["судак", "sudak"],
}

GOAL_TRANSLATE = {
    "flirt": "Флирт",
    "communication": "Общение",
    "friendship": "Дружба",
    "relationship": "Отношения"
}

def validate_age(age_str):
    try:
        age = int(age_str)
        return 18 <= age <= 99
    except ValueError:
        return False

def normalize_city(city):
    if not city:
        return city
    city_lower = city.lower().strip()
    for canonical, synonyms in CITY_SYNONYMS.items():
        if city_lower in synonyms or city_lower == canonical:
            return canonical
    return city_lower.capitalize()

def format_user_card(user, match_score=None):
    name_line = user.name or "Без имени"
    if user.is_premium:
        name_line += " ⭐"
    text = name_line + "\n"
    if user.age:
        text += f"Возраст: {user.age}\n"
    if user.city:
        text += f"Город: {user.city}\n"
    text += "---\n"
    if user.favorite_genres:
        text += f"Жанры: {user.favorite_genres}\n"
    if user.favorite_bands:
        text += f"Группы: {user.favorite_bands}\n"
    if user.favorite_songs:
        text += f"Песни: {user.favorite_songs}\n"
    text += "---\n"
    if user.search_goal:
        goal_ru = GOAL_TRANSLATE.get(user.search_goal, user.search_goal)
        text += f"Цель: {goal_ru}\n"
    text += "---\n"
    if user.interests:
        text += f"Интересы: {user.interests}\n"
    text += "---\n"
    if user.bio:
        text += f"{user.bio}\n"
    if match_score and match_score > 0:
        text += f"Совпадение вкуса: {round(match_score * 100)}%\n"
    return text

def format_profile(user):
    name_line = user.name or "Без имени"
    if user.is_premium:
        name_line += " ⭐"
    text = "Ваш профиль:\n\n"
    text += f"Имя: {name_line}\n"
    if user.age:
        text += f"Возраст: {user.age}\n"
    if user.city:
        text += f"Город: {user.city}\n"
    text += "---\n"
    if user.favorite_genres:
        text += f"Любимые жанры: {user.favorite_genres}\n"
    if user.favorite_bands:
        text += f"Любимые группы: {user.favorite_bands}\n"
    if user.favorite_songs:
        text += f"Любимые песни: {user.favorite_songs}\n"
    text += "---\n"
    if user.search_goal:
        goal_ru = GOAL_TRANSLATE.get(user.search_goal, user.search_goal)
        text += f"Цель знакомства: {goal_ru}\n"
    text += "---\n"
    if user.interests:
        text += f"Интересы: {user.interests}\n"
    text += "---\n"
    if user.bio:
        text += f"Био: {user.bio}\n"
    return text

async def send_security_notice_if_needed(message, user, session):
    if not user.last_security_notice or (datetime.utcnow() - user.last_security_notice) > timedelta(days=1):
        tip = random.choice(SECURITY_TIPS)
        await message.answer(tip)
        user.last_security_notice = datetime.utcnow()
        await session.commit()