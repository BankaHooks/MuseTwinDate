import random
from datetime import datetime, timedelta

SECURITY_TIPS = [
    "⚠️ Никогда не переводите деньги незнакомым людям.",
    "🔒 Не делитесь личными данными (адрес, паспорт, телефон).",
    "📸 Если просят фото с паспортом — мошенники.",
    "💬 Не переходите по подозрительным ссылкам.",
    "🚫 Если собеседник просит деньги — заблокируйте.",
    "🔐 Не передавайте доступ к вашему Telegram.",
    "📞 Не подтверждайте номера по SMS от незнакомцев.",
    "🛡️ Включите двухфакторную аутентификацию в Telegram.",
]

def validate_age(age_str: str) -> bool:
    try:
        age = int(age_str)
        return 18 <= age <= 99
    except ValueError:
        return False

def format_user_card(user, match_score: float = None) -> str:
    text = f"👤 {user.name or 'No name'}\n"
    if user.gender:
        text += f"⚥ {user.gender}\n"
    if user.age:
        text += f"🎂 {user.age} years old\n"
    if user.city:
        text += f"📍 {user.city}\n"
    if user.genre:
        text += f"🎵 {user.genre}\n"
    if user.favorite_band:
        text += f"🎤 {user.favorite_band}\n"
    if user.favorite_songs:
        text += f"🎧 {user.favorite_songs}\n"
    if user.bio:
        text += f"📝 {user.bio}\n"
    if match_score is not None and match_score > 0:
        text += f"🎯 Совпадение вкуса: {round(match_score * 100)}%\n"
    return text

def format_profile(user) -> str:
    text = "👤 Ваш профиль:\n\n"
    text += f"Имя: {user.name or 'Не указано'}\n"
    text += f"Пол: {user.gender or 'Не указан'}\n"
    text += f"Возраст: {user.age or 'Не указан'}\n"
    text += f"Город: {user.city or 'Не указан'}\n"
    text += f"Любимый жанр: {user.genre or 'Не указан'}\n"
    text += f"Любимая группа: {user.favorite_band or 'Не указана'}\n"
    text += f"Любимые песни: {user.favorite_songs or 'Не указаны'}\n"
    text += f"Ищу: {user.preferred_gender or 'Не указано'}\n"
    text += f"Био: {user.bio or 'Не указано'}\n"
    text += f"Премиум: {'✅' if user.is_premium else '❌'}"
    return text

async def send_security_notice_if_needed(message, user, session):
    if not user.last_security_notice or (datetime.utcnow() - user.last_security_notice) > timedelta(days=1):
        tip = random.choice(SECURITY_TIPS)
        await message.answer(tip)
        user.last_security_notice = datetime.utcnow()
        await session.commit()