import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

SIGN_EN = {
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
    sign_en = SIGN_EN.get(sign_ru)
    if not sign_en:
        return None
    url = f"https://aztro.sameerkumar.website/?sign={sign_en}&day=today"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Формируем красивое сообщение
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
                else:
                    logger.error(f"Horoscope API error: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Horoscope request failed: {e}")
        return None