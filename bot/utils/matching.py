import random
import re
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User

def _split_keywords(text: str) -> List[str]:
    if not text:
        return []
    items = re.split(r'[;,]\s*', text)
    return [item.strip().lower() for item in items if item.strip()]

async def pick_candidate_simple(session: AsyncSession, user: User) -> Tuple[Optional[User], float]:
    pool = await crud.get_candidate_pool(session, user.id)
    if not pool:
        return None, 0.0

    user_genres = set(_split_keywords(user.favorite_genres))
    user_bands = set(_split_keywords(user.favorite_bands))
    user_songs = set(_split_keywords(user.favorite_songs))
    user_interests = set(_split_keywords(user.interests))
    user_goal = user.search_goal

    scored = []
    for candidate in pool:
        score = 0.0

        cand_genres = set(_split_keywords(candidate.favorite_genres))
        if user_genres and cand_genres:
            common = user_genres & cand_genres
            if common:
                score += len(common) * 0.15
        if user.genre and candidate.genre and user.genre.lower() == candidate.genre.lower():
            score += 0.15

        cand_bands = set(_split_keywords(candidate.favorite_bands))
        if user_bands and cand_bands:
            common = user_bands & cand_bands
            if common:
                score += len(common) * 0.25
        if user.favorite_bands and candidate.favorite_bands and user.favorite_bands.lower() == candidate.favorite_bands.lower():
            score += 0.15

        cand_songs = set(_split_keywords(candidate.favorite_songs))
        if user_songs and cand_songs:
            common = user_songs & cand_songs
            if common:
                score += len(common) * 0.15

        cand_interests = set(_split_keywords(candidate.interests))
        if user_interests and cand_interests:
            common = user_interests & cand_interests
            if common:
                score += len(common) * 0.05

        if user_goal and candidate.search_goal and user_goal == candidate.search_goal:
            score += 0.1

        scored.append((candidate, min(score, 1.0)))

    if not scored:
        return random.choice(pool), 0.0

    max_score = max(s for _, s in scored)
    best_candidates = [c for c, s in scored if s == max_score]
    if max_score == 0:
        return random.choice(pool), 0.0
    chosen = random.choice(best_candidates)
    return chosen, max_score