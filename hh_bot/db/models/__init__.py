# Импортируем Base, чтобы он был доступен для Alembic
from ..base import Base

# Регистрация всех моделей для SQLAlchemy
from .user import User, SearchFilter, LLMSettings
from .vacancy import Vacancy, UserVacancyStatus
from ...enums import UserVacancyStatusEnum 
from .documents import GeneratedDocument

# Экспорт для Alembic и внешнего использования
__all__ = [
    "Base",  # <-- ДОБАВЛЕНО: Экспортируем Base
    "User", "SearchFilter", "LLMSettings",
    "Vacancy", "UserVacancyStatus",
    "GeneratedDocument"
]