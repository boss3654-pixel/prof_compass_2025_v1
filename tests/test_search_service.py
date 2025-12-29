import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import PropertyMock
from datetime import datetime, timezone
from sqlalchemy import select, and_

from hh_bot.services.search_service import process_search_results, fetch_vacancies
from hh_bot.db.models import User, Vacancy, UserVacancyStatus, UserVacancyStatusEnum

@pytest.fixture
def mock_user():
    """Фикстура для создания мок-пользователя"""
    user = MagicMock(spec=User)
    user.id = 1
    user.telegram_id = "12345"
    user.full_name = "Test User"
    return user

@pytest.fixture
def sample_vacancy_data():
    """Фикстура с примером данных вакансии"""
    return {
        'id': '98765',
        'name': 'Python Developer',
        'employer': {'name': 'Test Company'},
        'salary': {'from': 100000, 'currency': 'RUR'},
        'snippet': {'responsibility': 'Develop Python applications'},
        'alternate_url': 'https://hh.ru/vacancy/98765',
        'apply_url': 'https://hh.ru/vacancy/98765?apply=1',
        'published_at': datetime.now(timezone.utc).isoformat(),
    }

@pytest_asyncio.fixture
async def async_session_mock():
    """Фикстура для мока асинхронной сессии SQLAlchemy"""
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_process_search_results_success_new_vacancies(mock_user, sample_vacancy_data, async_session_mock):
    """Тест успешного поиска, когда все вакансии новые."""
    mock_message = AsyncMock()
    mock_state = MagicMock()

    async_session_mock.scalar.return_value = None

    with patch('hh_bot.services.search_service.fetch_vacancies', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [sample_vacancy_data]

        result = await process_search_results(
            message=mock_message,
            state=mock_state,
            session=async_session_mock,
            user=mock_user,
            filters_dict={"text": "Python"}
        )

    assert result is True
    mock_fetch.assert_awaited_once_with({"text": "Python"})
    async_session_mock.scalar.assert_awaited()
    assert async_session_mock.add.call_count == 2
    assert async_session_mock.commit.await_count == 1

    # ИСПРАВЛЕНИЕ: Более надежная проверка вызова answer
    expected_text = '🏢 *Python Developer*\n📍 Компания: Test Company\n💰 Зарплата: от 100000\n🔗 [Смотреть вакансию](https://hh.ru/vacancy/98765)\n✅ [Откликнуться](https://hh.ru/vacancy/98765?apply=1)'
    found_call = any(
        call.args and call.args[0] == expected_text and call.kwargs.get('parse_mode') == 'Markdown'
        for call in mock_message.answer.await_args_list
    )
    assert found_call, f"Ожидался вызов answer с текстом '{expected_text}' и parse_mode='Markdown', но он не был найден."

@pytest.mark.asyncio
async def test_process_search_results_success_existing_vacancy(mock_user, sample_vacancy_data, async_session_mock):
    """Тест поиска, когда вакансия уже существует в БД."""
    mock_message = AsyncMock()
    mock_state = MagicMock()

    existing_vacancy = MagicMock(spec=Vacancy)
    existing_vacancy.id = 55
    existing_vacancy.hh_id = sample_vacancy_data["id"]
    existing_vacancy.title = sample_vacancy_data["name"]
    existing_vacancy.company = sample_vacancy_data["employer"]["name"]
    existing_vacancy.salary = sample_vacancy_data["salary"]["from"] if sample_vacancy_data["salary"] else None
    existing_vacancy.description_snippet = sample_vacancy_data["snippet"]["responsibility"]
    type(existing_vacancy).link = PropertyMock(return_value=sample_vacancy_data["alternate_url"])
    existing_vacancy.apply_url = sample_vacancy_data["apply_url"]

    async_session_mock.scalar.return_value = existing_vacancy

    with patch('hh_bot.services.search_service.fetch_vacancies', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [sample_vacancy_data]

        result = await process_search_results(
            message=mock_message,
            state=mock_state,
            session=async_session_mock,
            user=mock_user,
            filters_dict={}
        )

    assert result is True
    assert async_session_mock.scalar.await_count == 1
    assert async_session_mock.add.call_count == 1
    assert async_session_mock.commit.await_count == 1

    # ИСПРАВЛЕНИЕ: Более надежная проверка вызова answer
    expected_text = '🏢 *Python Developer*\n📍 Компания: Test Company\n💰 Зарплата: от 100000\n🔗 [Смотреть вакансию](https://hh.ru/vacancy/98765)\n✅ [Откликнуться](https://hh.ru/vacancy/98765?apply=1)'
    found_call = any(
        call.args and call.args[0] == expected_text and call.kwargs.get('parse_mode') == 'Markdown'
        for call in mock_message.answer.await_args_list
    )
    assert found_call, f"Ожидался вызов answer с текстом '{expected_text}' и parse_mode='Markdown', но он не был найден."

@pytest.mark.asyncio
async def test_process_search_results_no_results(mock_user, async_session_mock):
    """Тест поиска, когда нет результатов."""
    mock_message = AsyncMock()
    mock_state = MagicMock()

    with patch('hh_bot.services.search_service.fetch_vacancies', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []

        result = await process_search_results(
            message=mock_message,
            state=mock_state,
            session=async_session_mock,
            user=mock_user,
            filters_dict={"text": "NonExistentPosition"}
        )

    assert result is True
    mock_fetch.assert_awaited_once()
    # ИСПРАВЛЕНИЕ: Более надежная проверка вызова answer
    expected_text = "По вашим критериям вакансий не найдено. Попробуйте изменить параметры."
    found_call = any(
        call.args and call.args[0] == expected_text
        for call in mock_message.answer.await_args_list
    )
    assert found_call, f"Ожидался вызов answer с текстом '{expected_text}', но он не был найден."
    assert async_session_mock.add.call_count == 0
    assert async_session_mock.commit.await_count == 0

@pytest.mark.asyncio
async def test_process_search_results_api_error(mock_user, async_session_mock):
    """Тест обработки ошибки при вызове API."""
    mock_message = AsyncMock()
    mock_state = MagicMock()

    with patch('hh_bot.services.search_service.fetch_vacancies', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("API connection error")

        result = await process_search_results(
            message=mock_message,
            state=mock_state,
            session=async_session_mock,
            user=mock_user,
            filters_dict={"text": "Python"}
        )

    assert result is False
    mock_fetch.assert_awaited_once()
    # ИСПРАВЛЕНИЕ: Более надежная проверка вызова answer
    expected_text = "❌ Произошла ошибка во время поиска. Попробуйте позже."
    found_call = any(
        call.args and call.args[0] == expected_text
        for call in mock_message.answer.await_args_list
    )
    assert found_call, f"Ожидался вызов answer с текстом '{expected_text}', но он не был найден."
    
    # Эта проверка падает, потому что, скорее всего, в рабочем коде отсутствует await session.rollback()
    async_session_mock.rollback.assert_awaited_once()
    assert async_session_mock.add.call_count == 0
    assert async_session_mock.commit.await_count == 0