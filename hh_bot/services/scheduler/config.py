from typing import Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

# Глобальные переменные для хранения экземпляров бота и сессии
_bot_instance: Optional[Bot] = None
_session_maker: Optional[async_sessionmaker] = None

def get_bot() -> Optional[Bot]:
    """Получает экземпляр бота."""
    return _bot_instance

def get_session_maker():
    """Получает session_maker."""
    return _session_maker

def set_bot_instance(bot: Bot):
    """Устанавливает экземпляр бота для использования в сервисе."""
    global _bot_instance
    _bot_instance = bot

def set_session_maker(session_maker: async_sessionmaker):
    """Устанавливает session_maker для создания сессий БД."""
    global _session_maker
    _session_maker = session_maker