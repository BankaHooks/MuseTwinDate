import logging
import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
from utils.vk_api import get_user_audio
from config import config

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "import_vk")
async def import_vk_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔗 Введите ссылку на ваш профиль VK (например, https://vk.com/id12345) или просто ID пользователя.\n\n"
        "Бот попытается получить до 10 ваших аудиозаписей и использовать их для подбора.\n"
        "Если профиль закрыт, вы сможете добавить песни вручную."
    )
    await state.set_state("vk_import_waiting")
    await callback.answer()

@router.message(F.text, F.state == "vk_import_waiting")
async def import_vk_process(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer("🔄 Обрабатываю запрос...")

    text = message.text.strip()
    user_id = None
    match = re.search(r'vk\.com/(id|club|public)(\d+)', text)
    if match:
        user_id = match.group(2)
    elif text.isdigit():
        user_id = text

    if not user_id:
        await message.answer("❌ Не удалось распознать ID. Попробуйте ещё раз или введите группы вручную.")
        await state.clear()
        return

    if not config.VK_ACCESS_TOKEN:
        await message.answer("❌ VK API не настроен. Пожалуйста, добавьте токен в настройках бота.")
        await state.clear()
        return

    await message.answer("🎵 Получаю ваши аудиозаписи из VK...")
    try:
        audio_list = await get_user_audio(user_id, config.VK_ACCESS_TOKEN, limit=10)
    except Exception as e:
        logger.error(f"VK import error: {e}")
        await message.answer(f"❌ Ошибка при запросе к VK: {e}")
        await state.clear()
        return

    if not audio_list:
        await message.answer(
            "❌ Не удалось получить аудиозаписи. Возможно, профиль закрыт или аудио недоступны.\n\n"
            "Вы можете добавить любимые песни вручную через редактирование профиля (кнопка «Песни»)."
        )
        await state.clear()
        return

    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Зарегистрируйтесь через /start")
        await state.clear()
        return

    songs = []
    bands = set()
    for audio in audio_list:
        artist = audio.get("artist", "")
        title = audio.get("title", "")
        if artist and title:
            songs.append(f"{artist} - {title}")
            bands.add(artist)

    songs_str = ", ".join(songs[:5])
    bands_str = ", ".join(list(bands)[:5])

    if not songs_str:
        await message.answer("❌ Не удалось извлечь песни из полученных данных.")
        await state.clear()
        return

    # Сохраняем в vk_audio, а не в favorite_songs
    await crud.update_user(session, user, vk_audio=songs_str)
    # Также добавляем группы из VK в favorite_bands? По условию не добавляем, пользователь сам вводит группы.
    # Но можно добавить как рекомендацию, но не сохранять автоматически. По твоему требованию мы не трогаем любимые группы.

    await message.answer(
        f"✅ Импортировано {len(songs)} песен из VK!\n\n"
        f"🎵 Мы проанализировали: {songs_str}\n\n"
        "Теперь бот будет учитывать их при поиске.\n"
        "Вы можете добавить любимые группы и песни вручную в профиле.",
        reply_markup=main_reply_keyboard()
    )
    await state.clear()