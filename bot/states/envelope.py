from aiogram.fsm.state import State, StatesGroup

class EnvelopeState(StatesGroup):
    text = State()