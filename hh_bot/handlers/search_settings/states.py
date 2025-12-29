from aiogram.fsm.state import State, StatesGroup

class SearchSettingsStates(StatesGroup):
    position = State()
    city = State()
    salary_min = State()
    remote = State()
    freshness_days = State()
    employment = State()
    confirmation = State()