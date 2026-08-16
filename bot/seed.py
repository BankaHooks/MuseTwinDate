import asyncio
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from config import config
from database.models import User, Base, Like, Skip, Block, Report, Chat, Payment
from keyboards.inline import INTEREST_CATEGORIES

NAMES = [
    "Алексей", "Мария", "Иван", "Екатерина", "Дмитрий", "Анна", "Сергей", "Ольга",
    "Андрей", "Наталья", "Максим", "Елена", "Владимир", "Ирина", "Павел", "Светлана",
    "Юрий", "Татьяна", "Артем", "Виктория", "Никита", "Анастасия", "Кирилл", "Дарья",
    "Глеб", "Варвара", "Михаил", "Полина", "Егор", "Алиса", "Роман", "София",
    "Даниил", "Арина", "Тимофей", "Ксения", "Матвей", "Илья", "Валерия",
    "Ярослав", "Алина", "Георгий", "Вероника", "Евгений", "Елизавета", "Николай", "Диана",
    "Василий", "Антонина", "Степан", "Злата", "Виталий", "Анжелика", "Олег", "Виолетта"
]

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород",
    "Челябинск", "Самара", "Омск", "Ростов-на-Дону", "Уфа", "Красноярск", "Пермь", "Воронеж",
    "Волгоград", "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск", "Барнаул", "Ульяновск",
    "Иркутск", "Хабаровск", "Ярославль", "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Новокузнецк", "Рязань", "Астрахань", "Пенза", "Липецк", "Калининград", "Курск", "Тверь",
    "Брянск", "Севастополь", "Симферополь", "Донецк", "Луганск", "Горловка", "Макеевка", "Евпатория",
    "Ялта", "Судак", "Псков", "Смоленск", "Благовещенск", "Сочи", "Анапа", "Геленджик"
]

GENRES = [
    "Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country",
    "Blues", "Metal", "Punk", "Reggae", "Folk", "Soul", "Funk", "Disco", "R&B", "Alternative"
]

BANDS = [
    "The Beatles", "Queen", "Nirvana", "Radiohead", "Coldplay", "Imagine Dragons",
    "Linkin Park", "Arctic Monkeys", "The Rolling Stones", "Pink Floyd", "Led Zeppelin",
    "The Weeknd", "Daft Punk", "Rammstein", "Metallica", "ABBA", "Depeche Mode",
    "The Smiths", "The Cure", "Joy Division", "New Order", "Kraftwerk", "Talking Heads",
    "The Strokes", "Interpol", "The Killers", "Muse", "Oasis", "Blur", "Pulp", "Suede",
    "Green Day", "Foo Fighters", "Pearl Jam", "Soundgarden", "Alice in Chains", "Stone Temple Pilots",
    "Red Hot Chili Peppers", "R.E.M.", "U2", "The Police", "The Who", "The Kinks",
    "The Doors", "Cream", "Jimi Hendrix Experience", "The Velvet Underground", "Pixies"
]

SONGS = [
    "Bohemian Rhapsody", "Imagine", "Hotel California", "Stairway to Heaven",
    "Smells Like Teen Spirit", "Billie Jean", "Hey Jude", "Yesterday",
    "Shape of You", "Uptown Funk", "Despacito", "Waka Waka",
    "Rolling in the Deep", "Someone Like You", "Bad Guy", "Blinding Lights",
    "Levitating", "Montero", "Stay", "Peaches",
    "Lose Yourself", "Stan", "The Real Slim Shady", "Without Me", "Rap God"
]

HOBBIES = [
    "путешествия", "чтение", "кино", "кулинария", "спорт", "танцы",
    "фотография", "музыка", "рисование", "настольные игры", "прогулки",
    "велосипед", "йога", "медитация", "игра на гитаре", "пение",
    "кулинарные эксперименты", "походы в горы", "вечерние прогулки", "киновечера"
]

GOALS = ["flirt", "communication", "friendship", "relationship"]
GOAL_RU = {
    "flirt": "флирта", "communication": "общения",
    "friendship": "дружбы", "relationship": "отношений"
}

EMOJIS = ["💕", "✨", "🍀", "🩷", "💌", "🌸", "❤️", "🫶", "🌟", "🎵", "🎶", "😊", "✌️", "👋", "☀️", "🌺", "🦋", "🐱", "🌙", "⭐"]

BIO_TEMPLATES = [
    "{name}, {age}, {city}. Ищу общение и дружбу. {hobby1}.",
    "{name}, {age}, {city}. Люблю {hobby1} и {hobby2}. Давай общаться! {emoji}",
    "{name}, {age}, {city}. Просто ищу классного собеседника. {emoji}",
    "{name} из {city}, {age} лет. Обожаю {hobby1}. В музыке — {music}. Пиши!",
    "{name}, {age}, {city}. Ищу единомышленников для {goal_ru}. {hobby1}.",
    "{name}, {age}, {city}. Увлекаюсь {hobby1}, {hobby2} и {hobby3}. Люблю {music}. {emoji}",
    "На связи {name}, {age}, {city}. Из хобби: {hobby1}, {hobby2}. Слушаю {music}. Жду твоего сообщения! {emoji}",
    "Я {name}, {age} лет, живу в {city}. Мне нравится {hobby1}, а ещё {hobby2}. Ищу {goal_ru}. {emoji}",
    "Здесь {name}, {age}. Люблю {hobby1} и {hobby2}. В музыке предпочитаю {music}. Ищу общение и дружбу. {emoji}",
    "{name}, {age}, {city}. Интересуюсь {interests}. В музыке — {music}. Буду рада новым знакомствам! {emoji}",
    "{name}, {age}, {city}. Обожаю {hobby1}, слушаю {music}. Ищу {goal_ru}. Пиши, не стесняйся! {emoji}",
    "",
    "",
    "{name}, {age}, {city}. Просто хочу пообщаться. 🫶",
    "{name}, {age}, {city}. {hobby1} – моё всё. Ищу компанию для прогулок и разговоров. {emoji}",
]

def generate_bio(name, age, city, music_text, interests_text, goal):
    template = random.choice(BIO_TEMPLATES)
    if not template:
        return ""
    hobby1 = random.choice(HOBBIES)
    hobby2 = random.choice([h for h in HOBBIES if h != hobby1])
    hobby3 = random.choice([h for h in HOBBIES if h not in (hobby1, hobby2)])
    emoji = random.choice(EMOJIS)
    goal_ru = GOAL_RU.get(goal, "знакомства")

    if interests_text and random.random() < 0.5:
        interests_part = interests_text
    else:
        interests_part = f"{hobby1}, {hobby2}"

    if not music_text:
        music_text = random.choice(GENRES)

    text = template.format(
        name=name,
        age=age,
        city=city,
        hobby1=hobby1,
        hobby2=hobby2,
        hobby3=hobby3,
        music=music_text,
        interests=interests_part,
        goal_ru=goal_ru,
        emoji=emoji
    )
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
        if not text.endswith((".", "!", "?")):
            text += "."
    return text

async def seed_users():
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        bots = await session.execute(select(User.id).where(User.telegram_id < 0))
        bot_ids = [row[0] for row in bots.all()]
        if bot_ids:
            await session.execute(delete(Like).where(Like.from_user_id.in_(bot_ids) | Like.to_user_id.in_(bot_ids)))
            await session.execute(delete(Skip).where(Skip.user_id.in_(bot_ids)))
            await session.execute(delete(Block).where(Block.blocker_id.in_(bot_ids) | Block.blocked_id.in_(bot_ids)))
            await session.execute(delete(Report).where(Report.reporter_id.in_(bot_ids) | Report.reported_id.in_(bot_ids)))
            await session.execute(delete(Chat).where(Chat.user1_id.in_(bot_ids) | Chat.user2_id.in_(bot_ids)))
            await session.execute(delete(Payment).where(Payment.user_id.in_(bot_ids)))
            await session.execute(delete(User).where(User.id.in_(bot_ids)))
            await session.commit()

        total = 15
        all_topics = []
        for topics in INTEREST_CATEGORIES.values():
            all_topics.extend(topics)

        for i in range(total):
            gender = random.choice(["Мужской", "Женский"])
            photo_id = random.randint(1, 100)
            photo_url = f"https://i.pravatar.cc/300?img={photo_id}"

            name = random.choice(NAMES)
            age = random.randint(18, 45)
            city = random.choice(CITIES)
            genre = random.choice(GENRES)
            band = random.choice(BANDS)
            song = random.choice(SONGS)
            pref_gender = random.choice(["Мужской", "Женский", "Любой"])
            goal = random.choice(GOALS)

            num_interests = random.randint(3, 5)
            selected_interests = []
            while len(selected_interests) < num_interests:
                topic = random.choice(all_topics)
                if topic not in selected_interests:
                    selected_interests.append(topic)
            interests_str = ", ".join(selected_interests)

            if random.random() < 0.5:
                music_text = f"{band} и {song}"
            else:
                music_text = genre

            bio = generate_bio(name, age, city, music_text, interests_str, goal)
            if not bio:
                bio = f"{name}, {age}, {city}." + (" Ищу общение!" if random.random() < 0.5 else "")

            user = User(
                telegram_id = -i - 1,
                username = f"user_{i}",
                name = name,
                gender = gender,
                age = age,
                city = city,
                favorite_genres = genre,
                favorite_bands = band,
                favorite_songs = song,
                preferred_gender = pref_gender,
                bio = bio,
                interests = interests_str,
                search_goal = goal,
                photo_file_id = photo_url,
                is_premium = random.choice([True, False, False, False, False]),
                created_at = datetime.utcnow()
            )
            session.add(user)
            if (i + 1) % 10 == 0:
                print(f"Создано {i+1} из {total} пользователей...")
        await session.commit()
    print(f"Готово! Создано {total} реалистичных анкет с фото.")

if __name__ == "__main__":
    asyncio.run(seed_users())