import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

GENRE_GROUPS = {
    "rock": ["alternative rock", "hard rock", "punk rock", "progressive rock",
             "psychedelic rock", "grunge", "indie rock", "post-rock",
             "russian rock", "classic rock", "folk rock", "symphonic rock"],
    "pop": ["russian pop", "k-pop", "j-pop", "pop rock", "synthpop",
            "dance pop", "electropop", "teen pop"],
    "electronic": ["techno", "house", "trance", "drum & bass", "dubstep",
                   "synthwave", "ambient", "electro", "idm", "breakbeat",
                   "hardstyle", "future bass"],
    "hip-hop/r&b": ["hip-hop", "russian rap", "r&b", "soul", "trap",
                    "grime", "g-funk", "lo-fi hip-hop", "alternative hip-hop"],
    "jazz/blues": ["jazz", "blues", "swing", "bebop", "fusion",
                   "blues rock", "soul blues", "dixieland", "acid jazz"],
    "classical/instrumental": ["classical", "instrumental", "orchestral", "piano",
                               "acoustic", "chamber music", "baroque", "romantic",
                               "minimalism"],
    "metal": ["metal", "heavy metal", "thrash metal", "death metal",
              "black metal", "power metal", "doom metal", "gothic metal",
              "folk metal", "nu-metal", "metalcore"],
    "folk/ethno": ["folk", "ethno", "celtic", "nordic folk", "balkan",
                   "african", "indian classical", "andean", "mongolian throat singing"],
    "alternative": ["indie", "alternative", "post-punk", "new wave", "shoegaze",
                    "dream pop", "noise rock", "math rock", "art rock"],
    "other": ["chanson", "reggae", "ska", "world", "soundtrack",
              "experimental", "spoken word", "comedy", "children's music"]
}

GENRE_TO_GROUP = {}
for group, subgenres in GENRE_GROUPS.items():
    for sub in subgenres:
        GENRE_TO_GROUP[sub] = group
for group in GENRE_GROUPS:
    GENRE_TO_GROUP[group] = group

def get_genre_group(genre: str) -> str:
    genre_lower = genre.lower().strip()
    return GENRE_TO_GROUP.get(genre_lower, genre_lower)

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

    score = 30 

    common_songs = songs1 & songs2
    score += len(common_songs) * 30

    common_bands = bands1 & bands2
    score += len(common_bands) * 20

    common_genres = genres1 & genres2
    score += len(common_genres) * 20

    remaining_genres1 = genres1 - common_genres
    remaining_genres2 = genres2 - common_genres
    groups1 = {get_genre_group(g) for g in remaining_genres1}
    groups2 = {get_genre_group(g) for g in remaining_genres2}
    common_groups = groups1 & groups2
    score += len(common_groups) * 20

    common_games = games1 & games2
    score += len(common_games) * 10

    common_interests = interests1 & interests2
    score += len(common_interests) * 5

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