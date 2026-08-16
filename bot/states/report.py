from aiogram.fsm.state import State, StatesGroup

class ReportState(StatesGroup):
    reason = State()
    description = State()