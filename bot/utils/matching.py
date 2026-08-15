import random
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User
from utils.music_engine import vector_from_json, engine

BASELINE_WEIGHT = 0.05


async def pick_candidate(session: AsyncSession, user: User) -> Tuple[Optional[User], float]:
    pool = await crud.get_candidate_pool(session, user.id)
    if not pool:
        return None, 0.0
    user_vector = vector_from_json(user.taste_vector)
    if not user_vector:
        return random.choice(pool), 0.0
    scored = [(c, engine.similarity(user_vector, vector_from_json(c.taste_vector))) for c in pool]
    candidates = [c for c, _ in scored]
    weights = [max(s, 0.0) + BASELINE_WEIGHT for _, s in scored]
    chosen = random.choices(candidates, weights=weights, k=1)[0]
    chosen_score = next(s for c, s in scored if c is chosen)
    return chosen, chosen_score
