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

# Локальные заглушки для каждого знака (упрощённые)
FALLBACK_HOROSCOPES = {
    "Овен": "Сегодня у вас будет много энергии. Используйте её для новых проектов. Любовь на горизонте.",
    "Телец": "День удачен для спокойных дел. Наслаждайтесь моментом.",
    "Близнецы": "Общение будет ключевым. Заводите новые знакомства.",
    "Рак": "Прислушайтесь к интуиции. Она вас не подведёт.",
    "Лев": "Ваша харизма сегодня на высоте. Привлекайте внимание!",
    "Дева": "Займитесь планированием. Это принесёт плоды.",
    "Весы": "Гармония и равновесие – ваш девиз на сегодня.",
    "Скорпион": "Страсть и интенсивность. Не бойтесь сильных эмоций.",
    "Стрелец": "Путешествия и приключения зовут. Рискните!",
    "Козерог": "Целеустремлённость приведёт к успеху.",
    "Водолей": "Нестандартные идеи сегодня в почёте.",
    "Рыбы": "День творчества и вдохновения. Мечтайте."
}

async def get_daily_horoscope(sign_ru: str) -> Optional[str]:
    sign_en = ZODIAC_SIGNS.get(sign_ru)
    if not sign_en:
        return None

    # Первый API (aztro)
    url1 = f"https://aztro.sameerkumar.website/?sign={sign_en}&day=today"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url1, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return format_horoscope(sign_ru, data)
    except Exception as e:
        logger.error(f"Horoscope API 1 failed: {e}")

    # Второй API (альтернативный)
    url2 = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign_en}&day=TODAY"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url2, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    horoscope_text = data.get("data", {}).get("horoscope_data", "")
                    if horoscope_text:
                        return f"🔮 Гороскоп для {sign_ru} на сегодня:\n\n{horoscope_text}"
    except Exception as e:
        logger.error(f"Horoscope API 2 failed: {e}")

    fallback_text = FALLBACK_HOROSCOPES.get(sign_ru, "Сегодня будет хороший день. Наслаждайтесь моментом.")
    return f"🔮 Гороскоп для {sign_ru} на сегодня (временная версия):\n\n{fallback_text}"

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