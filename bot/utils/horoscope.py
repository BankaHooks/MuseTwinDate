import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ZODIAC_SIGNS = {
    "Овен": "aries",
    "Телец": "taurus",
    "Близнецы": "gemini",
    "Рак": "cancer",
    "Лев": "leo",
    "Дева": "virgo",
    "Весы": "libra",
    "Скорпион": "scorpio",
    "Стрелец": "sagittarius",
    "Козерог": "capricorn",
    "Водолей": "aquarius",
    "Рыбы": "pisces"
}

async def get_daily_horoscope(sign_ru: str) -> Optional[str]:
    sign_en = ZODIAC_SIGNS.get(sign_ru)
    if not sign_en:
        return None

    # Первый API (aztro)
    url1 = f"https://aztro.sameerkumar.website/?sign={sign_en}&day=today"
    # Второй API (альтернативный)
    url2 = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign_en}&day=TODAY"

    # Пробуем первый
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url1) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return format_horoscope(sign_ru, data)
    except Exception as e:
        logger.error(f"Horoscope API 1 failed: {e}")

    # Пробуем второй
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # У второго API другой формат
                    horoscope_text = data.get("data", {}).get("horoscope_data", "")
                    if horoscope_text:
                        return f"🔮 Гороскоп для {sign_ru} на сегодня:\n\n{horoscope_text}"
    except Exception as e:
        logger.error(f"Horoscope API 2 failed: {e}")

    return None

def format_horoscope(sign_ru, data):
    message = (
        f"🔮 Гороскоп для {sign_ru} на сегодня:\n\n"
        f"{data.get('description', 'Нет описания')}\n\n"
        f"❤️ Любовь: {data.get('love', 'Нет данных')}\n"
        f"💼 Карьера: {data.get('career', 'Нет данных')}\n"
        f"💰 Финансы: {data.get('money', 'Нет данных')}\n"
        f"🍀 Удача: {data.get('luck', 'Нет данных')}\n"
        f"📅 Дата: {data.get('current_date', '')}"
    )
    return message