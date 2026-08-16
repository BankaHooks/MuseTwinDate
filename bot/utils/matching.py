import logging
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User

logger = logging.getLogger(__name__)

# Веса для расчёта совпадения (сумма = 1.0)
WEIGHT_SONGS = 0.30
WEIGHT_BANDS = 0.20
WEIGHT_GENRES = 0.15
WEIGHT_GAMES = 0.15
WEIGHT_INTERESTS = 0.10
WEIGHT_GOAL = 0.10

def jaccard_similarity(set1: set, set2: set) -> float:
    """Коэффициент Жаккара для множеств"""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def parse_comma_separated(text: str) -> set:
    """Разбивает строку с запятыми на множество, убирая лишние пробелы"""
    if not text:
        return set()
    return {item.strip().lower() for item in text.split(',') if item.strip()}

def calculate_match_score(user1: User, user2: User) -> float:
    """
    Рассчитывает оценку совпадения между двумя пользователями на основе музыкальных
    предпочтений и игр.
    """
    # Парсим поля пользователей
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

    # Совпадение по песням
    songs_score = jaccard_similarity(songs1, songs2)
    # Совпадение по группам
    bands_score = jaccard_similarity(bands1, bands2)
    # Совпадение по жанрам
    genres_score = jaccard_similarity(genres1, genres2)
    # Совпадение по играм
    games_score = jaccard_similarity(games1, games2)
    # Совпадение по интересам
    interests_score = jaccard_similarity(interests1, interests2)

    # Совпадение по цели (точное совпадение)
    goal_score = 1.0 if user1.search_goal and user2.search_goal and user1.search_goal == user2.search_goal else 0.0

    # Итоговый балл (взвешенная сумма)
    total_score = (
        songs_score * WEIGHT_SONGS +
        bands_score * WEIGHT_BANDS +
        genres_score * WEIGHT_GENRES +
        games_score * WEIGHT_GAMES +
        interests_score * WEIGHT_INTERESTS +
        goal_score * WEIGHT_GOAL
    )
    return total_score

async def pick_candidate_simple(session: AsyncSession, user: User) -> Tuple[Optional[User], Optional[float]]:
    """
    Простой алгоритм подбора кандидата: берём пул кандидатов, вычисляем оценку
    для каждого и возвращаем лучшего (с максимальной оценкой).
    """
    candidates = await crud.get_candidate_pool(session, user.id, limit=300)
    if not candidates:
        return None, None

    best_candidate = None
    best_score = -1.0

    for candidate in candidates:
        score = calculate_match_score(user, candidate)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    # Если лучший кандидат найден, создаём скип для него, чтобы не показывать повторно (но это уже делается в handlers)
    # Здесь просто возвращаем
    return best_candidate, round(best_score * 100) if best_score >= 0 else None