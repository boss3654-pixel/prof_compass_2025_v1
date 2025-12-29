# hh_bot/handlers/vacancies/search.py

from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...services.search_service import process_search_results
from ...db.models import User
from ...utils.logger import logger

# Роутер для поиска
search_router = Router()

# --- Словарь для сопоставления названий городов с ID в hh.ru ---
CITY_MAP = {
    "санкт-петербург": 2,
    "спб": 2,
    "москва": 1,
    "мск": 1,
    # ... добавьте другие города
}


# --- Состояния для нового поиска (с уникальными названиями) ---
class NewSearchStates(StatesGroup):
    search_position = State()  # <--- ИЗМЕНЕНО
    search_city = State()  # <--- ИЗМЕНЕНО
    search_salary_min = State()  # <--- ИЗМЕНЕНО


# --- Хэндлеры для нового поиска ---
@search_router.callback_query(F.data == "start_new_search")
async def start_new_search_flow(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс нового поиска, запрашивая должность."""
    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнем.\n\n"
        "Введите желаемую должность или ключевые слова для поиска (например, 'Python разработчик'):"
    )
    # <--- ИЗМЕНЕНО: Устанавливаем новое состояние
    await state.set_state(NewSearchStates.search_position)


# <--- ИЗМЕНЕНО: Декоратор и состояние
@search_router.message(NewSearchStates.search_position)
async def process_search_position(message: types.Message, state: FSMContext):
    """Сохраняет должность и запрашивает город."""
    await state.update_data(position=message.text)
    await message.answer("Хорошо. Теперь введите город для поиска:")
    # <--- ИЗМЕНЕНО: Устанавливаем новое состояние
    await state.set_state(NewSearchStates.search_city)


# <--- ИЗМЕНЕНО: Декоратор и состояние
@search_router.message(NewSearchStates.search_city)
async def process_search_city(message: types.Message, state: FSMContext):
    """Сохраняет город (по названию или ID) и запрашивает минимальную зарплату."""
    user_input = message.text.strip()
    city_id = None
    city_name_for_display = None

    if user_input.isdigit():
        city_id = int(user_input)
        city_name_for_display = f"с ID {city_id}"
        logger.info(f"Пользователь ввел числовой ID города: {city_id}")
    else:
        city_name_lower = user_input.lower()
        city_id = CITY_MAP.get(city_name_lower)
        if city_id:
            city_name_for_display = user_input.title()
            logger.info(f"Найден город '{user_input}' с ID {city_id}")

    if not city_id:
        await message.answer(
            "Извините, я не распознал город. Пожалуйста, введите название города (например, Санкт-Петербург) "
            "или его числовой ID (например, 2 для Санкт-Петербурга)."
        )
        return

    await state.update_data(city_id=city_id, city_name=city_name_for_display)
    await message.answer("Готово. Укажите минимальную зарплату (цифрами):")
    # <--- ИЗМЕНЕНО: Устанавливаем новое состояние
    await state.set_state(NewSearchStates.search_salary_min)


# <--- ИЗМЕНЕНО: Декоратор и состояние
@search_router.message(NewSearchStates.search_salary_min)
async def process_search_salary(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    """
    Финальный шаг: собирает все данные и вызывает сервис для обработки.
    """
    telegram_id_str = str(message.from_user.id)
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id_str))

    if not user:
        logger.error(
            f"Пользователь с ID {telegram_id_str} не найден в БД во время поиска!"
        )
        await message.answer("Произошла ошибка. Перезапустите бота с помощью /start.")
        await state.clear()
        return

    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите зарплату цифрами, без пробелов.")
        return

    await state.update_data(salary_min=int(message.text))
    search_data = await state.get_data()

    filters_dict = {
        "position": search_data.get("position"),
        "city_id": search_data.get("city_id"),
        "salary_min": search_data.get("salary_min"),
        "remote": False,
        "freshness_days": 30,
    }

    success = await process_search_results(
        message=message,
        state=state,
        session=session,
        user=user,
        filters_dict=filters_dict,
    )

    await state.clear()
