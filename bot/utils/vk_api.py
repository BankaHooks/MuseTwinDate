import aiohttp
import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from database.models import User

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/"

async def _vk_request(method: str, params: dict, token: str) -> dict:
    params["access_token"] = token
    params["v"] = "5.131"
    async with aiohttp.ClientSession() as session:
        async with session.get(VK_API_URL + method, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "error" in data:
                    logger.error(f"VK API error: {data['error']}")
                    return {}
                return data.get("response", {})
            else:
                logger.error(f"VK API HTTP error: {resp.status}")
                return {}

async def search_artist(artist_name: str, token: str) -> List[str]:
    params = {
        "q": artist_name,
        "type": "artist",
        "count": 10
    }
    result = await _vk_request("audio.search", params, token)
    items = result.get("items", [])
    artists = {}
    for item in items:
        artist = item.get("artist")
        if artist and artist not in artists:
            artists[artist] = True
    return list(artists.keys())

async def get_similar_artists(artist_name: str, token: str, limit: int = 5) -> List[str]:
    all_artists = await search_artist(artist_name, token)
    similar = [a for a in all_artists if a.lower() != artist_name.lower()]
    return similar[:limit]

async def enrich_profile_with_vk(user: User, session: AsyncSession, token: str):
    if not token:
        return
    if not user.favorite_bands:
        return
    bands = [b.strip() for b in user.favorite_bands.split(",") if b.strip()]
    if not bands:
        return
    artist = bands[0]
    similar = await get_similar_artists(artist, token, 5)
    if similar:
        existing = set(bands)
        new_bands = existing.union(similar)
        new_bands_str = ", ".join(new_bands)
        await crud.update_user(session, user, favorite_bands=new_bands_str)
        return similar
    return []

async def get_user_audio(user_id: str, token: str, limit: int = 10) -> List[Dict[str, str]]:
    params = {
        "owner_id": user_id,
        "count": limit,
        "need_video": 0
    }
    result = await _vk_request("audio.get", params, token)
    items = result.get("items", [])
    audio_list = []
    for item in items:
        audio_list.append({
            "artist": item.get("artist", ""),
            "title": item.get("title", ""),
            "url": item.get("url", "")
        })
    return audio_list