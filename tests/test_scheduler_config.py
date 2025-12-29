import pytest
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import async_sessionmaker

from hh_bot.services.scheduler.config import get_bot, set_bot_instance, get_session_maker, set_session_maker
import hh_bot.services.scheduler.config as config_module


def test_initial_state_is_none():
    """
    Проверяет, что начальное состояние модуля - None.
    """
    assert get_bot() is None
    assert get_session_maker() is None


def test_set_and_get_bot_instance():
    """
    Тест установки и получения экземпляра бота.
    """
    mock_bot = MagicMock()
    set_bot_instance(mock_bot)
    
    try:
        retrieved_bot = get_bot()
        assert retrieved_bot is mock_bot
        assert retrieved_bot is not None
    finally:
        # ИСПРАВЛЕНИЕ: Добавляем # type: ignore, чтобы отключить предупреждение
        # Это необходимый паттерн в тестах для сброса состояния.
        config_module._bot_instance = None # type: ignore


def test_set_and_get_session_maker():
    """
    Тест установки и получения session_maker.
    """
    mock_session_maker = MagicMock(spec=async_sessionmaker)
    set_session_maker(mock_session_maker)
    
    try:
        retrieved_maker = get_session_maker()
        assert retrieved_maker is mock_session_maker
        assert retrieved_maker is not None
    finally:
        # ИСПРАВЛЕНИЕ: Добавляем # type: ignore
        config_module._session_maker = None # type: ignore