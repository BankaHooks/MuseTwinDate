from aiogram.fsm.state import State, StatesGroup

class ProfileEdit(StatesGroup):
    name = State()
    age = State()
    city = State()
    genre = State()
    bio = State()
    photo = State()