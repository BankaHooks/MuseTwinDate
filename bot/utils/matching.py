import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

def calculate_match_score(user1: User, user2: User) -> float:
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

    # Песни: базовый бонус 30% + 3% за каждую совпавшую песню (макс 9%)
    common_songs = songs1 & songs2
    if common_songs:
        score += 30
        score += min(len(common_songs) * 3, 9)

    # Группы: базовый бонус 20% + 2% за каждую совпавшую группу (макс 6%)
    common_bands = bands1 & bands2
    if common_bands:
        score += 20
        score += min(len(common_bands) * 2, 6)

    # Жанры: базовый бонус 25% + 2% за каждый совпавший жанр (макс 6%)
    common_genres = genres1 & genres2
    if common_genres:
        score += 25
        score += min(len(common_genres) * 2, 6)

    # Игры: базовый бонус 10% + 1% за каждую совпавшую игру (макс 3%)
    common_games = games1 & games2
    if common_games:
        score += 10
        score += min(len(common_games) * 1, 3)

    # Интересы: базовый бонус 5% + 1% за каждый совпавший интерес (макс 3%)
    common_interests = interests1 & interests2
    if common_interests:
        score += 5
        score += min(len(common_interests) * 1, 3)

    # Цель: 5% если совпадает
    goal1 = normalize_goal(user1.search_goal)
    goal2 = normalize_goal(user2.search_goal)
    if goal1 and goal2 and goal1 == goal2:
        score += 5

    # Ограничиваем 100
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