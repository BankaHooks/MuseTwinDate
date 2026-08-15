import asyncio
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import config
from database.models import User, Base

# ----- Данные для генерации -----
NAMES = ["Алексей", "Мария", "Иван", "Екатерина", "Дмитрий", "Анна", "Сергей", "Ольга",
         "Андрей", "Наталья", "Максим", "Елена", "Владимир", "Ирина", "Павел", "Светлана",
         "Юрий", "Татьяна", "Артем", "Виктория", "Никита", "Анастасия", "Кирилл", "Дарья"]

CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород",
          "Челябинск", "Самара", "Омск", "Ростов-на-Дону", "Уфа", "Красноярск", "Пермь", "Воронеж"]

GENRES = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal"]

BANDS = ["The Beatles", "Queen", "Nirvana", "Radiohead", "Coldplay", "Imagine Dragons",
         "Linkin Park", "Arctic Monkeys", "The Rolling Stones", "Pink Floyd", "Led Zeppelin",
         "The Weeknd", "Daft Punk", "Rammstein", "Metallica", "ABBA", "Depeche Mode"]

SONGS = ["Bohemian Rhapsody", "Imagine", "Hotel California", "Stairway to Heaven",
         "Smells Like Teen Spirit", "Billie Jean", "Hey Jude", "Yesterday", "Shape of You",
         "Uptown Funk", "Despacito", "Waka Waka", "Rolling in the Deep", "Someone Like You",
         "Bad Guy", "Blinding Lights", "Levitating", "Montero", "Stay", "Peaches"]

BIOS = [
    "Люблю музыку и путешествия 🎸",
    "Ищу единомышленников для концертов",
    "Музыка — моя жизнь, джаз и рок в душе",
    "Обожаю электронную музыку и фестивали",
    "Ищу человека с похожим вкусом в музыке",
    "Гитара, уютные вечера и хороший саунд",
    "Фанат инди-культуры и нестандартных решений",
    "Классика в душе, рок в сердце",
    "Хип-хоп и ритм — моё всё",
    "Люблю открывать новую музыку и делиться ей"
]

PREFERRED_GENDERS = ["male", "female", "any"]

async def seed_users():
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for i in range(67):
            name = random.choice(NAMES)
            age = random.randint(18, 40)
            city = random.choice(CITIES)
            genre = random.choice(GENRES)
            band = random.choice(BANDS)
            songs = random.sample(SONGS, 2)
            songs_text = ", ".join(songs)
            bio = random.choice(BIOS)
            gender = random.choice(["male", "female"])
            pref_gender = random.choice(PREFERRED_GENDERS)

            user = User(
                telegram_id = -i - 1,
                username = f"user_{i}",
                name = name,
                gender = random.choice(["Мужской", "Женский"]),
                age = age,
                city = city,
                favorite_genres = genre,
                favorite_bands = band,
                favorite_songs = songs_text,
                preferred_gender = pref_gender,
                bio = bio,
                is_premium = random.choice([True, False, False, False]),  # 25% премиум
                created_at = datetime.utcnow()
            )
            session.add(user)
            if (i + 1) % 10 == 0:
                print(f"✅ Создано {i+1} пользователей...")
        await session.commit()
    print("🎉 Готово! Создано 67 тестовых анкет.")

if __name__ == "__main__":
    asyncio.run(seed_users())