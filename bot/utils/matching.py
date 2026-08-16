import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

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

    score = 0

    common_songs = songs1 & songs2
    if common_songs:
        score += 40
        score += min(len(common_songs) * 5, 15)
    else:
        pass

    common_bands = bands1 & bands2
    if common_bands:
        score += 30
        score += min(len(common_bands) * 3, 9)

    common_genres = genres1 & genres2
    if common_genres:
        score += 35
        score += min(len(common_genres) * 4, 12)

    common_games = games1 & games2
    if common_games:
        score += 15
        score += min(len(common_games) * 2, 6)

    common_interests = interests1 & interests2
    if common_interests:
        score += 10
        score += min(len(common_interests) * 1, 3)

    goal1 = normalize_goal(user1.search_goal)
    goal2 = normalize_goal(user2.search_goal)
    if goal1 and goal2 and goal1 == goal2:
        score += 5

    # Поднимаем минимум до 30, если есть хоть одно совпадение в музыке (песни/группы/жанры)
    has_music_match = bool(common_songs or common_bands or common_genres)
    if has_music_match and score < 40:
        score = 40
    elif not has_music_match and score < 30:
        score = 30

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