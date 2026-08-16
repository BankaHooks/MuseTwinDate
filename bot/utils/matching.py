import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.helpers import parse_comma_separated, normalize_goal

logger = logging.getLogger(__name__)

WEIGHT_SONGS = 0.30
WEIGHT_BANDS = 0.25
WEIGHT_GENRES = 0.25
WEIGHT_GAMES = 0.10
WEIGHT_INTERESTS = 0.10
WEIGHT_GOAL = 0.10

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

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

    songs_score = jaccard_similarity(songs1, songs2)
    bands_score = jaccard_similarity(bands1, bands2)
    genres_score = jaccard_similarity(genres1, genres2)
    games_score = jaccard_similarity(games1, games2)
    interests_score = jaccard_similarity(interests1, interests2)

    goal1 = normalize_goal(user1.search_goal)
    goal2 = normalize_goal(user2.search_goal)
    goal_score = 1.0 if goal1 and goal2 and goal1 == goal2 else 0.0

    total_score = (
        songs_score * WEIGHT_SONGS +
        bands_score * WEIGHT_BANDS +
        genres_score * WEIGHT_GENRES +
        games_score * WEIGHT_GAMES +
        interests_score * WEIGHT_INTERESTS +
        goal_score * WEIGHT_GOAL
    )
    return total_score

async def get_candidates_sorted(session: AsyncSession, user: User, limit: int = 5) -> List[Tuple[User, float]]:
    candidates = await crud.get_candidate_pool(session, user.id, limit=300)
    if not candidates:
        return []
    scored = []
    for candidate in candidates:
        score = calculate_match_score(user, candidate)
        scored.append((candidate, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]

async def pick_candidate_simple(session: AsyncSession, user: User) -> Tuple[Optional[User], Optional[float]]:
    scored = await get_candidates_sorted(session, user, limit=1)
    if scored:
        return scored[0][0], round(scored[0][1] * 100)
    return None, None