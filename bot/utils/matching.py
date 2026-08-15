import random
import re
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User

async def pick_candidate_simple(session: AsyncSession, user: User) -> Tuple[Optional[User], float]:
    pool = await crud.get_candidate_pool(session, user.id)
    if not pool:
        return None, 0.0

    user_keywords = set()
    if user.genre:
        user_keywords.add(user.genre.lower())
    if user.favorite_band:
        user_keywords.update(re.split(r'[,\s]+', user.favorite_band.lower()))
    if user.favorite_songs:
        user_keywords.update(re.split(r'[,\s]+', user.favorite_songs.lower()))

    scored = []
    for candidate in pool:
        score = 0.0
        cand_keywords = set()
        if candidate.genre:
            cand_keywords.add(candidate.genre.lower())
        if candidate.favorite_band:
            cand_keywords.update(re.split(r'[,\s]+', candidate.favorite_band.lower()))
        if candidate.favorite_songs:
            cand_keywords.update(re.split(r'[,\s]+', candidate.favorite_songs.lower()))

        common = user_keywords & cand_keywords
        if common:
            score = len(common) / max(len(user_keywords), 1)
        if user.genre and candidate.genre and user.genre.lower() == candidate.genre.lower():
            score += 0.3
        if user.favorite_band and candidate.favorite_band and user.favorite_band.lower() == candidate.favorite_band.lower():
            score += 0.5
        scored.append((candidate, min(score, 1.0)))

    if not scored:
        return random.choice(pool), 0.0

    max_score = max(s for _, s in scored)
    best_candidates = [c for c, s in scored if s == max_score]
    if max_score == 0:
        return random.choice(pool), 0.0
    chosen = random.choice(best_candidates)
    return chosen, max_score