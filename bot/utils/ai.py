import os
import json
import logging
from typing import List, Dict, Any, Optional
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessageRole
from database.models import User
from config import config

logger = logging.getLogger(__name__)

client = GigaChat(
    credentials=config.GIGACHAT_API_KEY,
    verify_ssl_certs=False,
    model=config.GIGACHAT_MODEL
)

async def generate_icebreakers(user1: User, user2: User) -> List[str]:
    prompt = (
        f"Пользователь 1: {user1.name or 'Без имени'}, любимые группы: {user1.favorite_bands or 'не указаны'}, "
        f"песни: {user1.favorite_songs or 'не указаны'}, жанры: {user1.favorite_genres or 'не указаны'}, "
        f"био: {user1.bio or 'не указано'}, интересы: {user1.interests or 'не указаны'}.\n"
        f"Пользователь 2: {user2.name or 'Без имени'}, любимые группы: {user2.favorite_bands or 'не указаны'}, "
        f"песни: {user2.favorite_songs or 'не указаны'}, жанры: {user2.favorite_genres or 'не указаны'}, "
        f"био: {user2.bio or 'не указано'}, интересы: {user2.interests or 'не указаны'}.\n\n"
        "Сгенерируй 5 персонализированных фраз для начала разговора, которые подойдут этим двоим. "
        "Учти их общие музыкальные вкусы, интересы и цели. Фразы должны быть естественными, дружелюбными и вовлекающими. "
        "Верни только список фраз, каждая с новой строки, без нумерации."
    )
    try:
        payload = Chat(
            messages=[Messages(role=MessageRole.USER, content=prompt)],
            temperature=0.8,
            max_tokens=200
        )
        response = await client.achat(payload)
        text = response.choices[0].message.content.strip()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines[:5]
    except Exception as e:
        logger.error(f"AI icebreakers failed: {e}")
        return ["Привет! Заметил, что мы оба любим музыку. Какую песню последнюю слушал?",]

async def analyze_music_taste(user: User) -> str:
    prompt = (
        f"Пользователь: {user.name or 'Без имени'}, любимые группы: {user.favorite_bands or 'не указаны'}, "
        f"песни: {user.favorite_songs or 'не указаны'}, жанры: {user.favorite_genres or 'не указаны'}, "
        f"био: {user.bio or 'не указано'}, интересы: {user.interests or 'не указаны'}.\n\n"
        "Напиши краткий (2-3 предложения) анализ музыкального вкуса этого человека. "
        "Опиши, какие направления ему близки, какой вайб он несёт, и что это говорит о его личности. "
        "Будь дружелюбным и интересным."
    )
    try:
        payload = Chat(
            messages=[Messages(role=MessageRole.USER, content=prompt)],
            temperature=0.7,
            max_tokens=120
        )
        response = await client.achat(payload)
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI music analysis failed: {e}")
        return "Анализ пока недоступен. Попробуй позже."

async def get_match_recommendation(user: User, candidates: List[User]) -> Dict[str, Any]:
    if not candidates:
        return {"user": None, "explanation": "Нет кандидатов для анализа."}
    top_candidates = candidates[:5]
    candidates_text = ""
    for i, u in enumerate(top_candidates, 1):
        candidates_text += (
            f"Кандидат {i}: {u.name or 'Без имени'}, группы: {u.favorite_bands or 'не указаны'}, "
            f"песни: {u.favorite_songs or 'не указаны'}, жанры: {u.favorite_genres or 'не указаны'}, "
            f"био: {u.bio or 'не указано'}, интересы: {u.interests or 'не указаны'}\n"
        )
    prompt = (
        f"Пользователь: {user.name or 'Без имени'}, любимые группы: {user.favorite_bands or 'не указаны'}, "
        f"песни: {user.favorite_songs or 'не указаны'}, жанры: {user.favorite_genres or 'не указаны'}, "
        f"био: {user.bio or 'не указано'}, интересы: {user.interests or 'не указаны'}.\n\n"
        f"Кандидаты:\n{candidates_text}\n"
        "Выбери одного кандидата, который лучше всего подходит этому пользователю. "
        "Учитывай общие музыкальные вкусы, интересы, цели и совместимость по био. "
        "Ответ должен быть в формате JSON с полями: 'best_index' (номер кандидата от 1 до N) и "
        "'explanation' (краткое объяснение, почему этот кандидат подходит, 2-3 предложения)."
        "Верни только JSON."
    )
    try:
        payload = Chat(
            messages=[Messages(role=MessageRole.USER, content=prompt)],
            temperature=0.5,
            max_tokens=150
        )
        response = await client.achat(payload)
        data = json.loads(response.choices[0].message.content.strip())
        idx = data.get("best_index", 1) - 1
        if 0 <= idx < len(top_candidates):
            return {"user": top_candidates[idx], "explanation": data.get("explanation", "Совпадение на основе музыкальных предпочтений.")}
        else:
            return {"user": None, "explanation": "Не удалось выбрать."}
    except Exception as e:
        logger.error(f"AI match recommendation failed: {e}")
        return {"user": None, "explanation": "Ошибка AI. Попробуй позже."}

async def generate_blind_date_questions(song: str, user1: User, user2: User) -> List[str]:
    prompt = (
        f"Для музыкального свидания вслепую выбрана песня: {song}.\n"
        f"Участник 1: {user1.name or 'Без имени'}, био: {user1.bio or 'не указано'}, интересы: {user1.interests or 'не указаны'}.\n"
        f"Участник 2: {user2.name or 'Без имени'}, био: {user2.bio or 'не указано'}, интересы: {user2.interests or 'не указаны'}.\n\n"
        "Сгенерируй 3 вопроса для обсуждения этой песни, которые помогут участникам лучше узнать друг друга. "
        "Вопросы должны быть открытыми, вовлекающими и связанными с музыкой, чувствами и личным опытом. "
        "Верни только список вопросов, каждый с новой строки, без нумерации."
    )
    try:
        payload = Chat(
            messages=[Messages(role=MessageRole.USER, content=prompt)],
            temperature=0.8,
            max_tokens=150
        )
        response = await client.achat(payload)
        text = response.choices[0].message.content.strip()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines[:3]
    except Exception as e:
        logger.error(f"AI blind date questions failed: {e}")
        return ["Что тебе больше всего нравится в этой песне?", "Какие эмоции она у тебя вызывает?", "С каким моментом жизни она ассоциируется?"]