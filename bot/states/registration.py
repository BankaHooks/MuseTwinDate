from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    genre = State()
    band = State()         
    preferred_gender = State()
    bio = State()
    photo = State()