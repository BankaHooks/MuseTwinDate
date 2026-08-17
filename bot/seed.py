import asyncio
from aiogram import Bot
from aiogram.types import InputFile
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
import os
from config import config
from database.models import User
from database.db import Base

USERS_DATA = [
    {
        "name": "Анна",
        "gender": "Женский",
        "age": 22,
        "city": "Москва",
        "genres": "Rock, Pop, Electronic",
        "bands": "The Beatles, Queen, Daft Punk",
        "songs": "Bohemian Rhapsody, Yesterday, Around the World",
        "goal": "Общение",
        "interests": "Кино, Книги, Путешествия",
        "games": "Minecraft, Among Us",
        "bio": "Люблю музыку, увлекаюсь фотографией. Ищу единомышленников.",
        "photo": "first.png",
        "telegram_id": -1
    },
    {
        "name": "Максим",
        "gender": "Мужской",
        "age": 25,
        "city": "Санкт-Петербург",
        "genres": "Jazz, Blues, Classical",
        "bands": "Miles Davis, Nina Simone, Chopin",
        "songs": "Kind of Blue, Feeling Good, Nocturne",
        "goal": "Дружба",
        "interests": "Музыка, Искусство, Прогулки",
        "games": "Rust, Valheim",
        "bio": "Джаз и классика — моя страсть. Ищу собеседников с похожим вкусом.",
        "photo": "second.png",
        "telegram_id": -2
    },
    {
        "name": "Екатерина",
        "gender": "Женский",
        "age": 21,
        "city": "Екатеринбург",
        "genres": "Pop, Indie, Russian Pop",
        "bands": "Billie Eilish, Arctic Monkeys, Монеточка",
        "songs": "bad guy, Do I Wanna Know?, каждый раз",
        "goal": "Флирт",
        "interests": "Сериалы, Танцы, Кофе",
        "games": "It Takes Two, Overcooked",
        "bio": "Люблю инди-музыку и атмосферные вечера. Ищу приключений.",
        "photo": "third.png",
        "telegram_id": -3
    },
    {
        "name": "Игорь",
        "gender": "Мужской",
        "age": 27,
        "city": "Новосибирск",
        "genres": "Metal, Heavy Metal, Thrash",
        "bands": "Metallica, Slayer, Iron Maiden",
        "songs": "Master of Puppets, Raining Blood, The Trooper",
        "goal": "Общение",
        "interests": "Гитара, Концерты, Спорт",
        "games": "Counter-Strike 2, Doom",
        "bio": "Металл — моя жизнь. Играю на гитаре. Жду единомышленников.",
        "photo": "fourth.png",
        "telegram_id": -4
    },
    {
        "name": "Ольга",
        "gender": "Женский",
        "age": 23,
        "city": "Казань",
        "genres": "Electronic, House, Synthwave",
        "bands": "Kraftwerk, Daft Punk, Justice",
        "songs": "Trans-Europe Express, One More Time, Genesis",
        "goal": "Отношения",
        "interests": "Синтезаторы, Киберпанк, Ночная жизнь",
        "games": "Cyberpunk 2077, Deus Ex",
        "bio": "Фанат электронной музыки и киберпанк-эстетики. Ищу собеседника для глубоких разговоров.",
        "photo": "fifth.png",
        "telegram_id": -5
    }
]

async def create_or_update_user(session: AsyncSession, bot: Bot, data: dict):
    """Создаёт или обновляет пользователя в БД, загружает фото и получает file_id."""
    telegram_id = data["telegram_id"]
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    # Загрузка фото
    photo_file_id = None
    photo_path = os.path.join("bots-photo", data["photo"])
    if os.path.exists(photo_path):
        try:
            admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
            if admin_id:
                with open(photo_path, 'rb') as f:
                    msg = await bot.send_photo(chat_id=admin_id, photo=InputFile(f))
                    photo_file_id = msg.photo[-1].file_id
                    # Удаляем сообщение, чтобы не засорять чат
                    await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                    print(f"Загружено фото для {data['name']}: {photo_file_id}")
            else:
                print("Нет ADMIN_IDS, пропускаем загрузку фото.")
        except Exception as e:
            print(f"Ошибка загрузки фото для {data['name']}: {e}")
    else:
        print(f"Файл {photo_path} не найден, пропускаем фото.")

    if user:
        user.username = f"test_{telegram_id}"  # можно задать уникальный username
        user.name = data["name"]
        user.gender = data["gender"]
        user.age = data["age"]
        user.city = data["city"]
        user.favorite_genres = data["genres"]
        user.favorite_bands = data["bands"]
        user.favorite_songs = data["songs"]
        user.search_goal = data["goal"]
        user.interests = data["interests"]
        user.favorite_games = data["games"]
        user.bio = data["bio"]
        if photo_file_id:
            user.photo_file_id = photo_file_id
        user.photo_local_path = photo_path if os.path.exists(photo_path) else None
        user.is_hidden = False
        user.is_banned = False
        print(f"Обновлён пользователь {data['name']} (telegram_id={telegram_id})")
    else:
        new_user = User(
            telegram_id=telegram_id,
            username=f"test_{telegram_id}",
            name=data["name"],
            gender=data["gender"],
            age=data["age"],
            city=data["city"],
            favorite_genres=data["genres"],
            favorite_bands=data["bands"],
            favorite_songs=data["songs"],
            search_goal=data["goal"],
            interests=data["interests"],
            favorite_games=data["games"],
            bio=data["bio"],
            photo_file_id=photo_file_id,
            photo_local_path=photo_path if os.path.exists(photo_path) else None,
            is_hidden=False,
            is_banned=False,
            is_premium=False
        )
        session.add(new_user)
        print(f"Создан пользователь {data['name']} (telegram_id={telegram_id})")

    await session.commit()

async def main():
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await session.execute(delete(User).where(User.telegram_id < 0))
        await session.commit()
        print("Старые тестовые пользователи удалены.")

        bot = Bot(token=config.BOT_TOKEN)
        try:
            for data in USERS_DATA:
                await create_or_update_user(session, bot, data)
        finally:
            await bot.session.close()

    print("Готово! Создано/обновлено 5 тестовых пользователей.")

if __name__ == "__main__":
    asyncio.run(main())