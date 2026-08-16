import json
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def get_embedding(text: str) -> Optional[List[float]]:
    if not text:
        return None
    return model.encode(text).tolist()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    a = np.array(vec1)
    b = np.array(vec2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

async def update_user_embedding(session: AsyncSession, user: User):
    parts = []
    if user.bio:
        parts.append(user.bio)
    if user.favorite_songs:
        parts.append(user.favorite_songs)
    if user.favorite_bands:
        parts.append(user.favorite_bands)
    if user.favorite_genres:
        parts.append(user.favorite_genres)
    if user.interests:
        parts.append(user.interests)
    text = " ".join(parts)
    if text:
        emb = get_embedding(text)
        if emb:
            user.embedding = json.dumps(emb)
            await session.commit()