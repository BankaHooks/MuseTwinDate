from aiogram.fsm.state import State, StatesGroup

class LikeMessageState(StatesGroup):
    text = State()