from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import crud
from keyboards.reply import main_reply_keyboard
import re

router = Router()

@router.callback_query(F.data == "import_vk")
async def import_vk_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ссылку на ваш профиль VK (например, https://vk.com/id12345) или просто ID пользователя.\n\n"
        "Бот попытается найти ваши публичные группы и добавить их в профиль.\n"
        "Если не получится, вы сможете добавить группы вручную."
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

    await message.answer(
        "К сожалению, автоматический импорт из VK требует авторизации (OAuth), которую мы пока не настроили.\n\n"
        "Вы можете добавить любимые группы вручную через редактирование профиля (кнопка «Группы»).\n"
        "Бот на основе введённых групп уже будет искать похожих исполнителей через VK."
    )
    await state.clear()