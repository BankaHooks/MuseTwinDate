from aiogram.fsm.state import State, StatesGroup

class Browse(StatesGroup):
    candidate_id = State()