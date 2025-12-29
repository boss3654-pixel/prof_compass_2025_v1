import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select

# Импорты из вашего приложения
from hh_bot.services.scheduler.jobs.constants import CITY_MAP
from hh_bot.db.models import User, SearchFilter

@pytest_asyncio.fixture
async def mock_bot():
    """Мок Telegram бота"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=12345, username="test_bot"))
    return bot

@pytest.fixture
def mock_fetch_vacancies(mocker):
    # Заменяем вызов функции ВНУТРИ модуля daily_digest
    return mocker.patch("hh_bot.services.scheduler.jobs.daily_digest.fetch_vacancies", new_callable=mocker.AsyncMock)

@pytest_asyncio.fixture
async def user_with_filter(async_session_maker):
    """Пользователь с фильтром для тестов"""
    async with async_session_maker() as session:
        # Проверяем существование пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == 123)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return existing_user.id
            
        # Создаем нового пользователя
        user = User(telegram_id=123, full_name="Test User")
        user.search_filters = SearchFilter(position="Python", city="Москва")
        session.add(user)
        await session.commit()
        return user.id