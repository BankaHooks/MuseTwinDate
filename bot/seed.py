import asyncio
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from config import config
from database.models import User, Base, Like, Skip, Block, Report, Chat, Payment
from keyboards.inline import INTEREST_CATEGORIES

# ----- ДАННЫЕ ДЛЯ ГЕНЕРАЦИИ АНКЕТ -----

NAMES = [
    "Алексей", "Мария", "Иван", "Екатерина", "Дмитрий", "Анна", "Сергей", "Ольга",
    "Андрей", "Наталья", "Максим", "Елена", "Владимир", "Ирина", "Павел", "Светлана",
    "Юрий", "Татьяна", "Артем", "Виктория", "Никита", "Анастасия", "Кирилл", "Дарья",
    "Глеб", "Варвара", "Михаил", "Полина", "Егор", "Алиса", "Роман", "София",
    "Даниил", "Арина", "Тимофей", "Ксения", "Матвей", "Алиса", "Илья", "Валерия",
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
    "The Doors", "Cream", "Jimi Hendrix Experience", "The Velvet Underground", "Pixies",
    "My Chemical Romance", "Fall Out Boy", "Panic! At The Disco", "Twenty One Pilots"
]

SONGS = [
    "Bohemian Rhapsody", "Imagine", "Hotel California", "Stairway to Heaven",
    "Smells Like Teen Spirit", "Billie Jean", "Hey Jude", "Yesterday",
    "Shape of You", "Uptown Funk", "Despacito", "Waka Waka",
    "Rolling in the Deep", "Someone Like You", "Bad Guy", "Blinding Lights",
    "Levitating", "Montero", "Stay", "Peaches",
    "Lose Yourself", "Stan", "The Real Slim Shady", "Without Me", "Rap God",
    "God's Plan", "Sicko Mode", "Goosebumps", "Magna Carta...", "Yeezus",
    "My Beautiful Dark Twisted Fantasy", "To Pimp a Butterfly", "good kid, m.A.A.d city",
    "The Dark Side of the Moon", "Wish You Were Here", "Animals", "The Wall",
    "Led Zeppelin IV", "Physical Graffiti", "Houses of the Holy", "Presence",
    "Back in Black", "Highway to Hell", "Thunderstruck",
    "Sweet Child O' Mine", "November Rain", "Welcome to the Jungle",
    "Enter Sandman", "Nothing Else Matters", "The Unforgiven",
    "Fade to Black", "Master of Puppets", "One", "For Whom the Bell Tolls",
    "Paranoid", "Iron Man", "War Pigs",
    "Kashmir", "Whole Lotta Love", "Rock and Roll", "Black Dog", "Immigrant Song",
    "The Ocean", "Misty Mountain Hop", "Comfortably Numb", "Another Brick in the Wall",
    "We Will Rock You", "We Are the Champions", "Don't Stop Me Now",
    "Somebody to Love", "Crazy Little Thing Called Love", "I Want to Break Free",
    "Radio Ga Ga", "Under Pressure", "Another One Bites the Dust",
    "Beat It", "Thriller", "Bad", "Smooth Criminal", "The Way You Make Me Feel",
    "Man in the Mirror", "Black or White", "Like a Rolling Stone", "Blowin' in the Wind",
    "The Times They Are a-Changin'", "Take It Easy", "Desperado", "New Kid in Town",
    "Lyin' Eyes", "Tequila Sunrise", "The Sound of Silence", "Mrs. Robinson",
    "Bridge over Troubled Water", "California Dreamin'", "Monday Monday",
    "I Got You Babe", "Good Vibrations", "Wouldn't It Be Nice", "God Only Knows",
    "Sloop John B", "Kokomo", "Surfin' USA", "I Heard It Through the Grapevine",
    "What's Going On", "Sexual Healing", "Let's Get It On", "Ain't No Mountain High Enough",
    "Respect", "Think", "Natural Woman", "Chain of Fools", "Son of a Preacher Man",
    "Piece of My Heart", "Proud Mary", "Rollin' on the River", "Fortunate Son",
    "Born to Run", "Thunder Road", "Badlands", "Hungry Heart", "Dancing in the Dark",
    "The River", "Born in the U.S.A.", "I'm on Fire", "Glory Days", "Paradise City",
    "Knockin' on Heaven's Door", "Don't Cry", "Livin' on a Prayer", "You Give Love a Bad Name",
    "It's My Life", "Bad Medicine", "Wanted Dead or Alive", "Blaze of Glory",
    "The Show Must Go On", "Love of My Life", "Killer Queen", "Bicycle Race",
    "Fat Bottomed Girls", "Creep", "High and Dry", "Fake Plastic Trees", "Karma Police",
    "Paranoid Android", "No Surprises", "Exit Music", "Street Spirit", "Pyramid Song",
    "Idioteque", "Everything in Its Right Place", "How to Disappear Completely",
    "There There", "2 + 2 = 5", "Jigsaw Falling into Place", "Reckoner", "House of Cards",
    "Videotape", "Lotus Flower", "Burn the Witch", "Daydreaming", "Present Tense",
    "True Love Waits", "Let Down", "The Bends", "My Iron Lung", "Just", "Planet Telex",
    "Black Star", "Sulk", "Bones", "Nice Dream", "The Tourist", "Climbing Up the Walls",
    "Electioneering", "Fitter Happier", "Subterranean Homesick Alien", "Airbag", "Lucky",
    "Meeting in the Aisle", "Pulk/Pull Revolving Doors", "Packt Like Sardines",
    "Knives Out", "Dollars and Cents", "I Might Be Wrong", "Life in a Glasshouse",
    "Morning Bell", "Like Spinning Plates", "A Punchup at a Wedding", "Myxomatosis",
    "Sit Down. Stand Up.", "Go to Sleep", "Where I End and You Begin",
    "We Suck Young Blood", "I Will", "A Wolf at the Door", "15 Step", "Bodysnatchers",
    "Nude", "Weird Fishes/Arpeggi", "All I Need", "Faust Arp", "Down Is the New Up",
    "4 Minute Warning", "Bloom", "Feral", "Little by Little", "Codex", "Give Up the Ghost",
    "Separator", "The Daily Mail", "Staircase", "Come to Your Senses"
]

TRAITS = [
    "весёлый", "добрый", "открытый", "романтичный", "энергичный",
    "спокойный", "целеустремлённый", "заботливый", "креативный", "надёжный",
    "общительный", "интеллектуальный", "чувствительный", "авантюрный", "оптимистичный",
    "нежный", "страстный", "загадочный", "харизматичный", "уверенный"
]

HOBBIES = [
    "путешествия", "чтение", "кино", "кулинария", "спорт", "танцы",
    "фотография", "музыка", "рисование", "настольные игры", "прогулки",
    "велосипед", "йога", "медитация", "игра на гитаре", "пение",
    "кулинарные эксперименты", "походы в горы", "вечерние прогулки", "киновечера"
]

SKILLS = [
    "играть на гитаре", "готовить пасту", "танцевать сальсу", "рисовать портреты",
    "писать стихи", "разговаривать на английском", "монтировать видео",
    "ухаживать за растениями", "разбираться в кофе", "запускать дрона",
    "кататься на сноуборде", "печь хлеб", "делать массаж", "играть в шахматы",
    "рассказывать анекдоты", "ориентироваться по звёздам", "заваривать чай"
]

QUALITIES = [
    "честность", "чувство юмора", "открытость", "забота", "надёжность",
    "верность", "романтичность", "интеллект", "страсть", "эмпатия",
    "целеустремлённость", "оптимизм", "нежность", "сила", "красота",
    "талант", "доброта", "щедрость", "любопытство", "самостоятельность"
]

GOALS = ["flirt", "communication", "friendship", "relationship"]

def generate_bio(name, age, city, genre, band, song, goals, hobbies_list, traits, skills, qualities):
    trait1 = random.choice(traits)
    trait2 = random.choice([t for t in traits if t != trait1])
    hobby1 = random.choice(hobbies_list)
    hobby2 = random.choice([h for h in hobbies_list if h != hobby1])
    hobby3 = random.choice([h for h in hobbies_list if h not in (hobby1, hobby2)])
    quality1 = random.choice(qualities)
    quality2 = random.choice([q for q in qualities if q != quality1])
    skill1 = random.choice(skills)
    goal = random.choice(goals)
    goal_text = {
        "flirt": "флирта", "communication": "общения",
        "friendship": "дружбы", "relationship": "отношений"
    }[goal]
    activity = random.choice(["прогулка", "чашка кофе", "вечер с музыкой", "поездка на природу"])

    parts = []
    intro = random.choice([
        f"Привет! Я {name}, {age} лет, {city}.",
        f"Меня зовут {name}, мне {age}, я из {city}.",
        f"Я {name}, {age} лет, живу в {city}.",
        f"Приветствую! Я {name}, {age} лет, {city}.",
        f"Я {name}, мне {age}, родился(ась) в {city}."
    ])
    parts.append(intro)
    if random.random() < 0.7:
        parts.append(f"Я {trait1} человек, люблю {hobby1} и {hobby2}.")
    else:
        parts.append(f"В душе я {trait1}, а в жизни {trait2}.")
    if random.random() < 0.6:
        parts.append(f"Моя любимая группа — {band}, а песня — {song}.")
    else:
        parts.append(f"Обожаю {band}, под {song} могу рыдать или танцевать.")
    parts.append(f"Ищу {goal_text} с человеком, который разделяет мои интересы.")
    parts.append(f"Ценю в людях {quality1} и {quality2}.")
    if random.random() < 0.5:
        parts.append(f"В свободное время я {hobby3}.")
    else:
        parts.append(f"Умею {skill1}.")
    parts.append(f"Буду рад(а) познакомиться и обсудить музыку за {activity}.")

    random.shuffle(parts)
    bio = " ".join(parts)
    bio = bio[0].upper() + bio[1:]
    if not bio.endswith("."):
        bio += "."
    return bio

async def seed_users():
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Сначала удаляем все связанные записи для болванок, а потом самих болванок
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

        total = 80
        photo_urls = []
        for i in range(1, 150, 3):
            photo_urls.append(f"https://randomuser.me/api/portraits/men/{i}.jpg")
            photo_urls.append(f"https://randomuser.me/api/portraits/women/{i+1}.jpg")
            photo_urls.append(f"https://randomuser.me/api/portraits/men/{i+2}.jpg")
        random.shuffle(photo_urls)

        all_topics = []
        for topics in INTEREST_CATEGORIES.values():
            all_topics.extend(topics)

        for i in range(total):
            gender = random.choice(["Мужской", "Женский"])
            photo_url = photo_urls[i % len(photo_urls)]
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

            bio = generate_bio(name, age, city, genre, band, song, [goal], HOBBIES, TRAITS, SKILLS, QUALITIES)

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
    print(f"Готово! Создано {total} реалистичных анкет с новыми интересами.")

if __name__ == "__main__":
    asyncio.run(seed_users())