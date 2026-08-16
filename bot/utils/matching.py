import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

def category_match_score(set1: set, set2: set, max_score: int) -> int:
    """Возвращает max_score, если пересечение не пусто, иначе 0."""
    if not set1 or not set2:
        return 0
    if set1 & set2:
        return max_score
    return 0

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
    score += category_match_score(songs1, songs2, 35)
    score += category_match_score(bands1, bands2, 25)
    score += category_match_score(genres1, genres2, 20)
    score += category_match_score(games1, games2, 10)
    score += category_match_score(interests1, interests2, 5)

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