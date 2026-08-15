from aiogram.fsm.state import State, StatesGroup

class ProfileEdit(StatesGroup):
    name = State()
    gender = State()
    age = State()
    city = State()
    genre = State()
    songs = State()
    band = State()
    preferred_gender = State()
    bio = State()
    photo = State()