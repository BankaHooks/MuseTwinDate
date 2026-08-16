import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

# Родственные группы жанров
GENRE_GROUPS = {
    "Rock": ["Alternative Rock", "Hard Rock", "Punk Rock", "Progressive Rock",
             "Psychedelic Rock", "Grunge", "Indie Rock", "Post-Rock",
             "Russian Rock", "Classic Rock", "Folk Rock", "Symphonic Rock"],
    "Pop": ["Russian Pop", "K-Pop", "J-Pop", "Pop Rock", "Synthpop",
            "Dance Pop", "Electropop", "Teen Pop"],
    "Electronic": ["Techno", "House", "Trance", "Drum & Bass", "Dubstep",
                   "Synthwave", "Ambient", "Electro", "IDM", "Breakbeat",
                   "Hardstyle", "Future Bass"],
    "Hip-Hop/R&B": ["Hip-Hop", "Russian Rap", "R&B", "Soul", "Trap",
                    "Grime", "G-Funk", "Lo-Fi Hip-Hop", "Alternative Hip-Hop"],
    "Jazz/Blues": ["Jazz", "Blues", "Swing", "Bebop", "Fusion",
                   "Blues Rock", "Soul Blues", "Dixieland", "Acid Jazz"],
    "Classical/Instrumental": ["Classical", "Instrumental", "Orchestral", "Piano",
                               "Acoustic", "Chamber Music", "Baroque", "Romantic",
                               "Minimalism"],
    "Metal": ["Metal", "Heavy Metal", "Thrash Metal", "Death Metal",
              "Black Metal", "Power Metal", "Doom Metal", "Gothic Metal",
              "Folk Metal", "Nu-Metal", "Metalcore"],
    "Folk/Ethno": ["Folk", "Ethno", "Celtic", "Nordic Folk", "Balkan",
                   "African", "Indian Classical", "Andean", "Mongolian Throat Singing"],
    "Alternative": ["Indie", "Alternative", "Post-Punk", "New Wave", "Shoegaze",
                    "Dream Pop", "Noise Rock", "Math Rock", "Art Rock"],
    "Other": ["Chanson", "Reggae", "Ska", "World", "Soundtrack",
              "Experimental", "Spoken Word", "Comedy", "Children's Music"]
}

# Обратный словарь: поджанр -> основная группа
GENRE_TO_GROUP = {}
for group, subgenres in GENRE_GROUPS.items():
    for sub in subgenres:
        GENRE_TO_GROUP[sub] = group
for group in GENRE_GROUPS:
    GENRE_TO_GROUP[group] = group

def get_genre_group(genre: str) -> str:
    return GENRE_TO_GROUP.get(genre, genre)

def calculate_match_score(user1: User, user2: User) -> int:
    # Парсим поля в множества (нижний регистр уже внутри parse_comma_separated)
    songs1 = parse_comma_separated(user1.favorite_songs)
    songs2 = parse_comma_separated(user2.favorite_songs)
    bands1 = parse_comma_separated(user1.favorite_bands)
    bands2 = parse_comma_separated(user2.favorite_bands)
    genres1 = parse_comma_separated(user1.favorite_genres)
    genres2 = parse_comma_separated(user2.favorite_genres)
    games1 = parse_comma_separated(user1.favorite_games)
    games2 = parse_comma_separated(user2.favorite_games)
    interests1 = parse_comma_separated(user1.interests)
    interests2 = parse_comma_separated(user2.interests)

    score = 30  # Базовый минимум

    # 1. Песни: +20% за каждую общую
    common_songs = songs1 & songs2
    score += len(common_songs) * 20

    # 2. Группы (исполнители): +15% за каждую общую
    common_bands = bands1 & bands2
    score += len(common_bands) * 15

    # 3. Жанры: точные совпадения +20% за каждый
    common_genres = genres1 & genres2
    score += len(common_genres) * 20

    # 4. Родственные группы жанров: +15% за каждую общую группу
    groups1 = {get_genre_group(g) for g in genres1}
    groups2 = {get_genre_group(g) for g in genres2}
    common_groups = groups1 & groups2
    score += len(common_groups) * 15

    # 5. Игры: +10% за каждую общую
    common_games = games1 & games2
    score += len(common_games) * 10

    # 6. Интересы: +5% за каждый общий
    common_interests = interests1 & interests2
    score += len(common_interests) * 5

    # 7. Цель: +5%, если совпадает
    goal1 = normalize_goal(user1.search_goal)
    goal2 = normalize_goal(user2.search_goal)
    if goal1 and goal2 and goal1 == goal2:
        score += 5

    return min(score, 100)

async def get_candidates_sorted(session: AsyncSession, user: User, limit: int = 5) -> List[Tuple[User, int]]:
    candidates = await crud.get_candidate_pool(session, user.id, limit=300)
    if not candidates:
        return []
    scored = []
    for candidate in candidates:
        score = calculate_match_score(user, candidate)
        scored.append((candidate, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]

async def pick_candidate_simple(session: AsyncSession, user: User) -> Tuple[Optional[User], Optional[int]]:
    scored = await get_candidates_sorted(session, user, limit=1)
    if scored:
        return scored[0][0], scored[0][1]
    return None, None