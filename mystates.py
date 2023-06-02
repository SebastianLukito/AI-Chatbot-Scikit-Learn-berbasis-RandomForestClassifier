from aiogram.dispatcher.filters import Text
from aiogram.types import ContentTypes
from aiogram.dispatcher.filters.state import StatesGroup, State


class MyStates(StatesGroup):
    waiting_for_response = State()
    waiting_for_context = State()
    waiting_for_fix = State()