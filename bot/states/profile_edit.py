from aiogram.fsm.state import State, StatesGroup

class ProfileEdit(StatesGroup):
    name = State()
    gender = State()
    age = State()
    city = State()
    genres = State()
    bands = State()
    songs = State()
    albums = State()
    artists = State()
    goal = State()
    interests = State()
    preferred_gender = State()
    bio = State()
    photo = State()