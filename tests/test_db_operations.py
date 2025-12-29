import sys
import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch, create_autospec

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from hh_bot.db.models import UserVacancyStatusEnum

# ИСПРАВЛЕНИЕ: Добавлен `# type: ignore` для отключения предупреждения о тестировании приватной функции
from hh_bot.services.scheduler.jobs.storage import (
    _format_salary_for_db, # type: ignore
    get_users_with_filters,
    find_and_process_new_vacancies,
    mark_vacancies_as_sent
)

@pytest.mark.parametrize("salary_data, expected", [
    ({'from': 100000, 'to': 150000, 'currency': 'RUR'}, "100000 - 150000 RUR"),
    ({'from': 100000, 'currency': 'USD'}, "от 100000 USD"),
    ({'to': 150000, 'currency': 'EUR'}, "до 150000 EUR"),
    (None, None),
    ({}, None)
])
def test_format_salary_for_db(salary_data, expected):
    assert _format_salary_for_db(salary_data) == expected

@pytest_asyncio.fixture
def mock_async_session_maker():
    """
    ФИНАЛЬНОЕ РЕШЕНИЕ: Используем create_autospec для правильного API
    и ЯВНО настраиваем его как асинхронный контекстный менеджер.
    Это решает проблему с `async with`.
    """
    # 1. Создаем мок, который идеально повторяет API AsyncSession
    mock_session = create_autospec(AsyncSession, instance=True)
    
    # 2. КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Явно делаем мок асинхронным контекстным менеджером.
    # __aenter__ должен вернуть саму сессию.
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # 3. Создаем мок для фабрики.
    factory_mock = MagicMock(return_value=mock_session)
    
    return factory_mock

@pytest.mark.asyncio
async def test_get_users_with_filters(mock_async_session_maker):
    """Тестирует получение пользователей с фильтрами."""
    
    # Настраиваем мок сессии, который возвращает наша фабрика
    mock_session = mock_async_session_maker.return_value
    mock_user = MagicMock()
    
    # Создаем мок для результата, который вернет execute
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_user]
    
    # Устанавливаем этот мок как результат вызова async-метода execute
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемую функцию, передавая ей мок-фабрику
    users = await get_users_with_filters(mock_async_session_maker)
    
    # Проверяем, что был вызван execute с правильным запросом
    mock_session.execute.assert_called_once()
    # Проверяем, что результат был преобразован в список и содержит одного пользователя
    assert len(users) == 1
    assert users[0] == mock_user

@pytest.mark.asyncio
async def test_find_new_vacancies_one_new(mock_async_session_maker):
    """Тестирует случай, когда найдена одна новая вакансия."""
    
    # Настраиваем мок сессии
    mock_session = mock_async_session_maker.return_value
    mock_session.execute.side_effect = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))), # Существующие вакансии
        MagicMock(all=MagicMock(return_value=[])) # Отправленные вакансии
    ]
    
    vacancies_data = [{
        'id': '123',
        'name': 'Dev',
        'employer': {'name': 'Company'},
        'salary': {'from': 100000, 'to': 150000, 'currency': 'RUR'},
        'alternate_url': 'url',
        'snippet': {'responsibility': 'code'},
        'published_at': datetime.now(timezone.utc).isoformat()
    }]
    
    # Вызываем функцию, передавая ей мок-сессию напрямую
    result = await find_and_process_new_vacancies(mock_session, 1, vacancies_data)
    
    assert len(result) == 1
    assert result[0][1]['id'] == '123'
    # Проверяем, что новая вакансия была добавлена в сессию
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once() # flush теперь тоже AsyncMock, и это сработает

@pytest.mark.asyncio
@patch('hh_bot.services.scheduler.jobs.storage.UserVacancyStatus', new_callable=MagicMock)
async def test_mark_vacancies_as_sent(mock_uvs_class, mock_async_session_maker):
    """Тестирует пометку вакансий как отправленных."""
    
    # Настраиваем мок сессии
    mock_session = mock_async_session_maker.return_value
    mock_vacancy = MagicMock(id=1)
    
    # Вызываем функцию, передавая ей мок-сессию напрямую
    await mark_vacancies_as_sent(mock_session, 1, [mock_vacancy])
    
    # Проверяем, что session.add был вызван один раз
    mock_session.add.assert_called_once()
    
    # Проверяем, что наш мок-класс UserVacancyStatus был вызван один раз с нужными параметрами
    mock_uvs_class.assert_called_once_with(
        user_id=1,
        vacancy_id=1,
        status=UserVacancyStatusEnum.SENT
    )