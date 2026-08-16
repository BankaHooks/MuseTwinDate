import asyncio
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from config import config
from database.models import User, Base

NAMES = ["Алексей", "Мария", "Иван", "Екатерина", "Дмитрий", "Анна", "Сергей", "Ольга",
         "Андрей", "Наталья", "Максим", "Елена", "Владимир", "Ирина", "Павел", "Светлана",
         "Юрий", "Татьяна", "Артем", "Виктория", "Никита", "Анастасия", "Кирилл", "Дарья",
         "Глеб", "Варвара", "Михаил", "Полина", "Егор", "Алиса", "Роман", "София"]

CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород",
          "Челябинск", "Самара", "Омск", "Ростов-на-Дону", "Уфа", "Красноярск", "Пермь", "Воронеж",
          "Волгоград", "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск", "Барнаул", "Ульяновск",
          "Иркутск", "Хабаровск", "Ярославль", "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово"]

GENRES = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal",
          "Punk", "Reggae", "Folk", "Soul", "Funk", "Disco"]

BANDS = ["The Beatles", "Queen", "Nirvana", "Radiohead", "Coldplay", "Imagine Dragons",
         "Linkin Park", "Arctic Monkeys", "The Rolling Stones", "Pink Floyd", "Led Zeppelin",
         "The Weeknd", "Daft Punk", "Rammstein", "Metallica", "ABBA", "Depeche Mode",
         "The Smiths", "The Cure", "Joy Division", "New Order", "Kraftwerk", "Talking Heads",
         "The Strokes", "Interpol", "The Killers", "Muse", "Oasis", "Blur", "Pulp", "Suede"]

SONGS = ["Bohemian Rhapsody", "Imagine", "Hotel California", "Stairway to Heaven",
         "Smells Like Teen Spirit", "Billie Jean", "Hey Jude", "Yesterday", "Shape of You",
         "Uptown Funk", "Despacito", "Waka Waka", "Rolling in the Deep", "Someone Like You",
         "Bad Guy", "Blinding Lights", "Levitating", "Montero", "Stay", "Peaches",
         "Lose Yourself", "Stan", "The Real Slim Shady", "Without Me", "Rap God",
         "God's Plan", "Sicko Mode", "Goosebumps", "Magna Carta...", "Yeezus",
         "My Beautiful Dark Twisted Fantasy", "To Pimp a Butterfly", "good kid, m.A.A.d city",
         "The Dark Side of the Moon", "Wish You Were Here", "Animals", "The Wall",
         "Led Zeppelin IV", "Physical Graffiti", "Houses of the Holy", "Presence"]

BIOS = [
    "Люблю музыку и путешествия",
    "Ищу единомышленников для концертов",
    "Музыка — моя жизнь, джаз и рок в душе",
    "Обожаю электронную музыку и фестивали",
    "Ищу человека с похожим вкусом в музыке",
    "Гитара, уютные вечера и хороший саунд",
    "Фанат инди-культуры и нестандартных решений",
    "Классика в душе, рок в сердце",
    "Хип-хоп и ритм — моё всё",
    "Люблю открывать новую музыку и делиться ей",
    "Мой мир — это звуки и эмоции",
    "Ищу родственную душу через музыку",
    "Меломан с 90-х",
    "Без музыки жить не могу",
    "Вечный поиск идеального саундтрека"
]

PREFERRED_GENDERS = ["Мужской", "Женский", "Любой"]

async def seed_users():
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        existing = await session.execute(select(User).where(User.telegram_id < 0))
        existing_count = len(existing.scalars().all())
        if existing_count > 0:
            print(f"В базе уже есть {existing_count} тестовых анкет.")
            answer = input("Удалить их и создать заново? (y/n): ")
            if answer.lower() == 'y':
                await session.execute(delete(User).where(User.telegram_id < 0))
                await session.commit()
                print("Старые анкеты удалены.")
            else:
                print("Создание новых анкет отменено.")
                return

        total = 50
        for i in range(total):
            gender = random.choice(["Мужской", "Женский"])
            photo_id = random.randint(1, 99)
            if gender == "Мужской":
                photo_url = f"https://randomuser.me/api/portraits/men/{photo_id}.jpg"
            else:
                photo_url = f"https://randomuser.me/api/portraits/women/{photo_id}.jpg"

            name = random.choice(NAMES)
            age = random.randint(18, 45)
            city = random.choice(CITIES)
            genre = random.choice(GENRES)
            band = random.choice(BANDS)
            songs = random.sample(SONGS, 3)
            songs_text = ", ".join(songs)
            bio = random.choice(BIOS)
            pref_gender = random.choice(PREFERRED_GENDERS)

            user = User(
                telegram_id = -i - 1,
                username = f"user_{i}",
                name = name,
                gender = gender,
                age = age,
                city = city,
                favorite_genres = genre,
                favorite_bands = band,
                favorite_songs = songs_text,
                preferred_gender = pref_gender,
                bio = bio,
                photo_file_id = photo_url,
                is_premium = random.choice([True, False, False, False, False]),
                created_at = datetime.utcnow()
            )
            session.add(user)
            if (i + 1) % 10 == 0:
                print(f"Создано {i+1} из {total} пользователей...")
        await session.commit()
    print(f"Готово! Создано {total} тестовых анкет с портретами людей (пол соответствует фото).")

if __name__ == "__main__":
    asyncio.run(seed_users())