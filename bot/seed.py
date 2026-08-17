import asyncio
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from database.models import User
from database.db import Base, DATABASE_URL
from utils.helpers import normalize_city
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройте подключение к БД (используем существующий DATABASE_URL из config)
from config import config
DATABASE_URL = config.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Здесь вы заполняете данные для 10 пользователей
USERS_DATA = [
    {
        "username": "user1",
        "name": "Анна",
        "gender": "Женский",
        "age": 22,
        "city": "Москва",
        "favorite_genres": "Pop, Electronic, Indie",
        "favorite_bands": "The Weeknd, Dua Lipa, Billie Eilish",
        "favorite_songs": "Blinding Lights, Levitating, Bad Guy",
        "search_goal": "Общение",
        "interests": "Кино, Путешествия, Фотография",
        "bio": "Люблю музыку и хорошие фильмы. Ищу новых друзей.",
        "photo_path": None,  # укажите путь к фото, например "photos/anna.jpg" или оставьте None
    },
    # ... добавьте ещё 9 пользователей
]

async def create_user(session: AsyncSession, data: dict):
    # Проверяем, есть ли уже такой username (чтобы не дублировать)
    stmt = select(User).where(User.username == data["username"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        logger.info(f"Пользователь {data['username']} уже существует, пропускаем")
        return None

    # Если фото указано, пробуем прочитать и сохранить file_id (но это требует загрузки в Telegram)
    # Для простоты мы будем сохранять только локальный путь, а file_id не заполняем.
    user = User(
        telegram_id=random.randint(100000000, 999999999),  # случайный ID, но лучше использовать отрицательные числа для ботов
        username=data["username"],
        name=data["name"],
        gender=data["gender"],
        age=data["age"],
        city=normalize_city(data["city"]),
        favorite_genres=data["favorite_genres"],
        favorite_bands=data["favorite_bands"],
        favorite_songs=data["favorite_songs"],
        search_goal=data["search_goal"],
        interests=data["interests"],
        bio=data["bio"],
        photo_local_path=data.get("photo_path"),
        photo_file_id=None,  # не загружаем в Telegram
        is_hidden=False,
        is_banned=False,
        is_premium=False,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
    )
    session.add(user)
    await session.commit()
    logger.info(f"Создан пользователь {user.name} ({user.username})")
    return user

async def main():
    async with async_session() as session:
        for data in USERS_DATA:
            await create_user(session, data)
    logger.info("Готово!")

if __name__ == "__main__":
    asyncio.run(main())