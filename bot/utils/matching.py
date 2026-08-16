import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

# Родственные группы жанров (поджанры)
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

    common_songs = songs1 & songs2
    common_bands = bands1 & bands2
    common_genres = genres1 & genres2
    common_games = games1 & games2
    common_interests = interests1 & interests2

    # Родственные жанры (поджанры) – исключаем точные и считаем общие группы
    remaining_genres1 = genres1 - common_genres
    remaining_genres2 = genres2 - common_genres
    groups1 = {}
    for g in remaining_genres1:
        group = get_genre_group(g)
        groups1.setdefault(group, set()).add(g)
    groups2 = {}
    for g in remaining_genres2:
        group = get_genre_group(g)
        groups2.setdefault(group, set()).add(g)
    common_groups = set(groups1.keys()) & set(groups2.keys())
    related_count = 0
    for group in common_groups:
        count1 = len(groups1.get(group, set()))
        count2 = len(groups2.get(group, set()))
        related_count += min(count1, count2)

    # Базовый минимум 30%
    score = 30

    # Бонусы с ограничениями
    bonus_songs = min(len(common_songs) * 10, 30)
    bonus_bands = min(len(common_bands) * 8, 24)
    bonus_genres_exact = min(len(common_genres) * 6, 18)
    bonus_genres_related = min(related_count * 3, 9)
    bonus_games = min(len(common_games) * 5, 15)
    bonus_interests = min(len(common_interests) * 2, 10)

    goal1 = normalize_goal(user1.search_goal)
    goal2 = normalize_goal(user2.search_goal)
    bonus_goal = 5 if (goal1 and goal2 and goal1 == goal2) else 0

    total_bonus = (bonus_songs + bonus_bands + bonus_genres_exact +
                   bonus_genres_related + bonus_games + bonus_interests + bonus_goal)

    score += total_bonus
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