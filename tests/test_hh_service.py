import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import json
import aiohttp

from hh_bot.services.hh_service import fetch_vacancies

MINIMAL_SUCCESS_RESPONSE = {
    "found": 1,
    "items": [{
        "id": "123",
        "name": "Python Developer",
        "employer": {"name": "Test Company"},
        "alternate_url": "http://example.com",
        "published_at": "2023-01-01T00:00:00+0300"
    }],
    "pages": 1,
    "page": 0,
    "per_page": 50
}

EMPTY_RESPONSE = {
    "found": 0,
    "items": [],
    "pages": 0,
    "page": 0,
    "per_page": 50
}

@pytest_asyncio.fixture
async def mock_session():
    """Фикстура для мокирования aiohttp.ClientSession"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=MINIMAL_SUCCESS_RESPONSE)
        mock_response.raise_for_status = MagicMock()  # Синхронный метод
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        yield mock_get, mock_response

@pytest.mark.asyncio
@pytest.mark.parametrize("filters, expected_params, response_data, expected_count, exception", [
    # Успешный сценарий
    (
        {"position": "Python"},
        {'text': 'Python', 'area': None, 'salary': None, 'only_with_salary': 'false', 
         'schedule': None, 'period': 1, 'employment': None, 'experience': None, 'per_page': 50},
        MINIMAL_SUCCESS_RESPONSE,
        1,
        None
    ),
    # Пустой результат
    (
        {"position": "NonExistentJob"},
        {'text': 'NonExistentJob', 'area': None, 'salary': None, 'only_with_salary': 'false', 
         'schedule': None, 'period': 1, 'employment': None, 'experience': None, 'per_page': 50},
        EMPTY_RESPONSE,
        0,
        None
    ),
    # HTTP ошибка
    (
        {"position": "Python"},
        {'text': 'Python', 'area': None, 'salary': None, 'only_with_salary': 'false', 
         'schedule': None, 'period': 1, 'employment': None, 'experience': None, 'per_page': 50},
        None,
        0,
        aiohttp.ClientResponseError(MagicMock(), tuple(), status=500)
    ),
    # Ошибка JSON
    (
        {"position": "Python"},
        {'text': 'Python', 'area': None, 'salary': None, 'only_with_salary': 'false', 
         'schedule': None, 'period': 1, 'employment': None, 'experience': None, 'per_page': 50},
        None,
        0,
        json.JSONDecodeError("Invalid JSON", "", 0)
    )
])
async def test_fetch_vacancies_scenarios(filters, expected_params, response_data, expected_count, exception, mock_session, caplog):
    mock_get, mock_response = mock_session
    
    # Настройка мока для различных сценариев
    if exception:
        if isinstance(exception, aiohttp.ClientResponseError):
            mock_response.raise_for_status.side_effect = exception
        elif isinstance(exception, json.JSONDecodeError):
            mock_response.json.side_effect = exception
    elif response_data:
        mock_response.json.return_value = response_data
    
    result = await fetch_vacancies(filters)
    
    # Проверка вызова с правильными параметрами
    mock_get.assert_called_once()
    call_args = mock_get.call_args[1]
    params = call_args.get('params', {})
    for key, value in expected_params.items():
        assert params.get(key) == value
    
    # Проверка результата
    assert len(result) == expected_count
    
    # Дополнительная проверка для сценария с ошибкой
    if exception and isinstance(exception, aiohttp.ClientResponseError):
        assert "Ошибка при запросе к API hh.ru" in caplog.text