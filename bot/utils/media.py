import os
from config import config
from aiogram.types import PhotoSize

MEDIA_DIR = config.MEDIA_DIR
os.makedirs(MEDIA_DIR, exist_ok=True)

async def save_photo(file: PhotoSize, user_id: int) -> str:
    file_info = await file.bot.get_file(file.file_id)
    file_path = f"{MEDIA_DIR}/user_{user_id}_{file.file_id}.jpg"
    await file.bot.download_file(file_info.file_path, file_path)
    return file_path