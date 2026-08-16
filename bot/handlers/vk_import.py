from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
from utils.vk_api import get_user_audio
from config import config
import re

router = Router()

@router.callback_query(F.data == "import_vk")
async def import_vk_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ссылку на ваш профиль VK (например, https://vk.com/id12345) или просто ID пользователя.\n\n"
        "Бот попытается получить до 10 ваших аудиозаписей и добавить их в профиль.\n"
        "Если профиль закрыт, вы сможете добавить песни вручную."
    )
    await state.set_state("vk_import_waiting")
    await callback.answer()

@router.message(F.text, F.state == "vk_import_waiting")
async def import_vk_process(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip()
    user_id = None
    match = re.search(r'vk\.com/(id|club|public)(\d+)', text)
    if match:
        user_id = match.group(2)
    elif text.isdigit():
        user_id = text

    if not user_id:
        await message.answer("Не удалось распознать ID. Попробуйте ещё раз или введите группы вручную.")
        await state.clear()
        return

    if not config.VK_ACCESS_TOKEN:
        await message.answer("VK API не настроен. Пожалуйста, добавьте токен в настройках.")
        await state.clear()
        return

    await message.answer("🔄 Получаю ваши аудиозаписи из VK...")
    audio_list = await get_user_audio(user_id, config.VK_ACCESS_TOKEN, limit=10)

    if not audio_list:
        await message.answer(
            "Не удалось получить аудиозаписи. Возможно, профиль закрыт или аудио недоступны.\n\n"
            "Вы можете добавить любимые песни вручную через редактирование профиля (кнопка «Песни»)."
        )
        await state.clear()
        return

    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Зарегистрируйтесь через /start")
        await state.clear()
        return

    # Формируем строки для сохранения
    songs = []
    bands = set()
    for audio in audio_list:
        artist = audio.get("artist", "")
        title = audio.get("title", "")
        if artist and title:
            songs.append(f"{artist} - {title}")
            bands.add(artist)

    songs_str = ", ".join(songs[:5])  # сохраним до 5 песен
    bands_str = ", ".join(list(bands)[:5])  # до 5 групп

    if not songs_str:
        await message.answer("Не удалось извлечь песни.")
        await state.clear()
        return

    # Обновляем профиль
    await crud.update_user(session, user, favorite_songs=songs_str)
    if bands_str:
        # Добавляем группы (если есть)
        existing_bands = set([b.strip() for b in (user.favorite_bands or "").split(",") if b.strip()])
        existing_bands.update([b.strip() for b in bands_str.split(",") if b.strip()])
        new_bands_str = ", ".join(existing_bands)
        await crud.update_user(session, user, favorite_bands=new_bands_str)

    await message.answer(
        f"✅ Импортировано {len(songs)} песен!\n\n"
        f"Любимые песни: {songs_str}\n"
        f"Группы: {bands_str}\n\n"
        "Вы всегда можете отредактировать их в профиле.",
        reply_markup=main_reply_keyboard()
    )
    await state.clear()