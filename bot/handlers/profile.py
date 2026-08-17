from typing import Union
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database import crud
from database.models import User
from keyboards.inline import (
    profile_main_keyboard, profile_edit_keyboard, gender_choose_keyboard,
    genre_category_keyboard, genre_items_keyboard,
    goal_keyboard, interest_category_keyboard,
    interest_items_keyboard, games_category_keyboard, games_items_keyboard,
    preferred_gender_keyboard, profile_search_settings_keyboard
)
from keyboards.reply import main_reply_keyboard
from states.profile_edit import ProfileEditState
from utils.helpers import validate_age, normalize_city, format_profile, validate_text_length
from utils.security import escape_markdown
import logging

logger = logging.getLogger(__name__)
router = Router()

async def edit_or_caption(callback: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    text = format_profile(user)
    markup = profile_main_keyboard()
    if user.photo_file_id:
        await callback.message.edit_media(
            InputMediaPhoto(media=user.photo_file_id, caption=text),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

async def show_profile_for_message(message: Message, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Зарегистрируйтесь через /start")
        return
    text = format_profile(user)
    markup = profile_main_keyboard()
    if user.photo_file_id:
        await message.answer_photo(photo=user.photo_file_id, caption=text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)

@router.callback_query(F.data == "profile_back")
async def profile_back(callback: CallbackQuery, session: AsyncSession):
    await show_profile(callback, session)

@router.callback_query(F.data == "profile_edit_menu")
async def profile_edit_menu(callback: CallbackQuery):
    await edit_or_caption(callback, "Выберите поле для редактирования:", reply_markup=profile_edit_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("edit_"))
async def start_edit(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    field_map = {
        "name": ("Введите новое имя:", ProfileEditState.name),
        "age": ("Введите новый возраст (16-99):", ProfileEditState.age),
        "city": ("Введите новый город:", ProfileEditState.city),
        "genres": ("Выберите категорию жанров:", ProfileEditState.genres),
        "bands": ("Введите новые группы (до 5, через запятую):", ProfileEditState.bands),
        "songs": ("Введите новые песни (до 500 символов):", ProfileEditState.songs),
        "goal": ("Выберите новую цель:", ProfileEditState.goal),
        "interests": ("Выберите новые интересы:", ProfileEditState.interests),
        "games": ("Выберите новые игры:", ProfileEditState.games),
        "bio": ("Введите новое био (до 500 символов):", ProfileEditState.bio),
        "photo": ("Отправьте новое фото:", ProfileEditState.photo),
        "preferred_gender": ("Выберите предпочитаемый пол партнёра:", ProfileEditState.preferred_gender),
    }
    if field not in field_map:
        await callback.answer("Неизвестное поле")
        return
    prompt, state_name = field_map[field]
    await state.set_state(state_name)
    await state.update_data(edit_field=field)
    if field == "genres":
        await edit_or_caption(callback, "Выберите категорию жанров:", reply_markup=genre_category_keyboard())
    elif field == "goal":
        await edit_or_caption(callback, prompt, reply_markup=goal_keyboard())
    elif field == "interests":
        await edit_or_caption(callback, "Выберите категорию интересов:", reply_markup=interest_category_keyboard())
    elif field == "games":
        await edit_or_caption(callback, "Выберите категорию игр:", reply_markup=games_category_keyboard())
    elif field == "preferred_gender":
        await edit_or_caption(callback, prompt, reply_markup=preferred_gender_keyboard())
    elif field == "photo":
        await edit_or_caption(callback, "Отправьте фото (или нажмите «Пропустить»):",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                  [InlineKeyboardButton(text="Пропустить", callback_data="skip_photo_edit")]
                              ]))
    else:
        await edit_or_caption(callback, prompt)
    await callback.answer()

@router.callback_query(F.data == "skip_photo_edit", StateFilter(ProfileEditState.photo))
async def skip_photo_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await finish_edit(callback, state, session, photo_file_id=None)

@router.message(ProfileEditState.name)
async def edit_name(message: Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    if not name or len(name) > 100:
        await message.answer("Имя должно быть от 1 до 100 символов.")
        return
    await state.update_data(name=name)
    await finish_edit(message, state, session)

@router.message(ProfileEditState.age)
async def edit_age(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        await message.answer("Введите число.")
        return
    age = int(message.text)
    if not validate_age(age):
        await message.answer("Возраст должен быть от 16 до 99 лет.")
        return
    await state.update_data(age=age)
    await finish_edit(message, state, session)

@router.message(ProfileEditState.city)
async def edit_city(message: Message, state: FSMContext, session: AsyncSession):
    city = normalize_city(message.text.strip())
    if not city:
        await message.answer("Город не может быть пустым.")
        return
    await state.update_data(city=city)
    await finish_edit(message, state, session)

# === Обработчики для жанров ===
@router.callback_query(F.data.startswith("genre_cat_"), StateFilter(ProfileEditState.genres))
async def edit_genre_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("genre_cat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    await state.update_data(current_genre_category=category)
    markup = genre_items_keyboard(category, selected)
    await edit_or_caption(callback, f"Выберите жанры в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("genre_item_"), StateFilter(ProfileEditState.genres))
async def edit_genre_item(callback: CallbackQuery, state: FSMContext):
    genre = callback.data[len("genre_item_"):]
    genre = genre.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if genre in selected:
        selected.remove(genre)
        await callback.answer(f"Удалено: {genre}")
    else:
        if len(selected) >= 15:
            await callback.answer("Максимум 15 жанров.", show_alert=True)
            return
        selected.append(genre)
        await callback.answer(f"Добавлено: {genre}")
    await state.update_data(selected_genres=selected)
    category = data.get("current_genre_category", "")
    if category:
        markup = genre_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "genre_back", StateFilter(ProfileEditState.genres))
async def edit_genre_back(callback: CallbackQuery, state: FSMContext):
    await edit_or_caption(callback, "Выберите категорию жанров:", reply_markup=genre_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "genres_done", StateFilter(ProfileEditState.genres))
async def edit_genres_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if not selected:
        await callback.answer("Выберите хотя бы один жанр!", show_alert=True)
        return
    await state.update_data(genres=", ".join(selected))
    await finish_edit(callback, state, session)

@router.message(ProfileEditState.bands)
async def edit_bands(message: Message, state: FSMContext, session: AsyncSession):
    bands = message.text.strip()
    if bands:
        band_list = [b.strip() for b in bands.split(",") if b.strip()]
        if len(band_list) > 5:
            await message.answer("Не более 5 групп. Напишите снова.")
            return
        await state.update_data(bands=", ".join(band_list[:5]))
    else:
        await state.update_data(bands="")
    await finish_edit(message, state, session)

@router.message(ProfileEditState.songs)
async def edit_songs(message: Message, state: FSMContext, session: AsyncSession):
    songs = message.text.strip()
    if songs and not validate_text_length(songs, 500):
        await message.answer("Слишком длинный текст (максимум 500 символов).")
        return
    await state.update_data(songs=songs)
    await finish_edit(message, state, session)

@router.callback_query(F.data.startswith("goal_"), StateFilter(ProfileEditState.goal))
async def edit_goal(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    goal = callback.data.split("_")[1]
    goal_map = {
        "flirt": "Флирт",
        "communication": "Общение",
        "friendship": "Дружба",
        "relationship": "Отношения"
    }
    await state.update_data(goal=goal_map.get(goal, goal))
    await finish_edit(callback, state, session)

# === Предпочитаемый пол партнёра (ИСПРАВЛЕН) ===
@router.callback_query(F.data.startswith("pref_gender_"), StateFilter(ProfileEditState.preferred_gender))
async def set_preferred_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    # Исправлено: берём последний элемент после разделения, потому что callback_data = "pref_gender_Мужской"
    gender = callback.data.split("_", 2)[2]  # или split("_")[2]
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        user.preferred_gender = gender
        await session.commit()
        await callback.answer(f"Пол установлен: {gender}")
        await callback.message.delete()
        await show_profile(callback, session)
    else:
        await callback.answer("Ошибка")

# === Обработчики для интересов ===
@router.callback_query(F.data.startswith("cat_"), StateFilter(ProfileEditState.interests))
async def edit_interest_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("cat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    await state.update_data(current_category=category)
    markup = interest_items_keyboard(category, selected)
    await edit_or_caption(callback, f"Выберите интересы в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("interest_"), StateFilter(ProfileEditState.interests))
async def edit_interest_item(callback: CallbackQuery, state: FSMContext):
    item = callback.data[len("interest_"):]
    item = item.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    if item in selected:
        selected.remove(item)
        await callback.answer(f"Удалено: {item}")
    else:
        if len(selected) >= 10:
            await callback.answer("Максимум 10 интересов.", show_alert=True)
            return
        selected.append(item)
        await callback.answer(f"Добавлено: {item}")
    await state.update_data(selected_interests=selected)
    category = data.get("current_category", "")
    if category:
        markup = interest_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "interests_back", StateFilter(ProfileEditState.interests))
async def edit_interests_back(callback: CallbackQuery, state: FSMContext):
    await edit_or_caption(callback, "Выберите категории интересов:", reply_markup=interest_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "interests_done", StateFilter(ProfileEditState.interests))
async def edit_interests_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected = data.get("selected_interests", [])
    if not selected:
        await callback.answer("Выберите хотя бы один интерес!", show_alert=True)
        return
    await state.update_data(interests=", ".join(selected))
    await finish_edit(callback, state, session)

# === Обработчики для игр ===
@router.callback_query(F.data.startswith("gamecat_"), StateFilter(ProfileEditState.games))
async def edit_games_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("gamecat_"):]
    category = category.replace('_', ' ').strip()
    data = await state.get_data()
    selected = data.get("selected_games", [])
    await state.update_data(current_game_category=category)
    markup = games_items_keyboard(category, selected)
    await edit_or_caption(callback, f"Выберите игры в категории «{category}»:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("game_"), StateFilter(ProfileEditState.games))
async def edit_game_item(callback: CallbackQuery, state: FSMContext):
    game = callback.data[len("game_"):]
    game = game.replace('_', ' ')
    data = await state.get_data()
    selected = data.get("selected_games", [])
    if game in selected:
        selected.remove(game)
        await callback.answer(f"Удалено: {game}")
    else:
        if len(selected) >= 10:
            await callback.answer("Максимум 10 игр.", show_alert=True)
            return
        selected.append(game)
        await callback.answer(f"Добавлено: {game}")
    await state.update_data(selected_games=selected)
    category = data.get("current_game_category", "")
    if category:
        markup = games_items_keyboard(category, selected)
        await callback.message.edit_reply_markup(reply_markup=markup)

@router.callback_query(F.data == "games_back", StateFilter(ProfileEditState.games))
async def edit_games_back(callback: CallbackQuery, state: FSMContext):
    await edit_or_caption(callback, "Выберите категории игр:", reply_markup=games_category_keyboard())
    await callback.answer()

@router.callback_query(F.data == "games_none", StateFilter(ProfileEditState.games))
async def edit_games_none(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(games="Не играю")
    await finish_edit(callback, state, session)

@router.callback_query(F.data == "games_done", StateFilter(ProfileEditState.games))
async def edit_games_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected = data.get("selected_games", [])
    if not selected:
        await callback.answer("Выберите хотя бы одну игру или нажмите «Не играю».", show_alert=True)
        return
    await state.update_data(games=", ".join(selected))
    await finish_edit(callback, state, session)

@router.message(ProfileEditState.bio)
async def edit_bio(message: Message, state: FSMContext, session: AsyncSession):
    bio = message.text.strip()
    if bio and not validate_text_length(bio, 500):
        await message.answer("Био не может быть длиннее 500 символов.")
        return
    await state.update_data(bio=bio)
    await finish_edit(message, state, session)

@router.message(ProfileEditState.photo)
async def edit_photo(message: Message, state: FSMContext, session: AsyncSession):
    if not message.photo:
        await message.answer("Отправьте фото (или нажмите «Пропустить»).")
        return
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await finish_edit(message, state, session)

@router.callback_query(F.data == "profile_search_settings")
async def profile_search_settings(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Зарегистрируйтесь через /start")
        return
    markup = profile_search_settings_keyboard(user)
    await edit_or_caption(callback, "Настройки поиска:", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "toggle_city")
async def toggle_city(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        user.search_city_only = not user.search_city_only
        await session.commit()
        await callback.answer(f"Поиск {'только в городе' if user.search_city_only else 'везде'}")
        await profile_search_settings(callback, session)

@router.callback_query(F.data == "toggle_hide")
async def toggle_hide(callback: CallbackQuery, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        user.is_hidden = not user.is_hidden
        await session.commit()
        await callback.answer(f"Анкета {'скрыта' if user.is_hidden else 'показана'}")
        await profile_search_settings(callback, session)

@router.callback_query(F.data == "reset_profile")
async def reset_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        user.name = None
        user.gender = None
        user.age = None
        user.city = None
        user.favorite_genres = None
        user.favorite_bands = None
        user.favorite_songs = None
        user.search_goal = None
        user.interests = None
        user.favorite_games = None
        user.bio = None
        user.photo_file_id = None
        await session.commit()
        await callback.answer("Профиль сброшен. Начните заново через /start")
        await callback.message.delete()

@router.callback_query(F.data == "refresh_recommendations")
async def refresh_recommendations(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("Рекомендации обновлены!")

async def finish_edit(event: Union[Message, CallbackQuery], state: FSMContext, session: AsyncSession, **extra):
    data = await state.get_data()
    user = await crud.get_user_by_telegram_id(session, event.from_user.id)
    if not user:
        if isinstance(event, CallbackQuery):
            await event.answer("Ошибка")
        else:
            await event.reply("Ошибка")
        return
    update_data = {}
    for key in ["name", "age", "city", "genres", "bands", "songs", "goal", "interests", "games", "bio", "photo_file_id", "preferred_gender"]:
        if key in data:
            update_data[key] = data[key]
    if extra:
        update_data.update(extra)
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    # Явное сохранение полей с несовпадающими именами
    if "genres" in data:
        user.favorite_genres = data["genres"]
    if "bands" in data:
        user.favorite_bands = data["bands"]
    if "songs" in data:
        user.favorite_songs = data["songs"]
    if "goal" in data:
        user.search_goal = data["goal"]
    if "games" in data:
        user.favorite_games = data["games"]
    if "preferred_gender" in data:
        user.preferred_gender = data["preferred_gender"]
    await session.commit()
    await state.clear()
    if isinstance(event, Message):
        await event.reply("Профиль обновлён!")
        await show_profile_for_message(event, session)
    else:
        await event.answer("Профиль обновлён!")
        await show_profile(event, session)