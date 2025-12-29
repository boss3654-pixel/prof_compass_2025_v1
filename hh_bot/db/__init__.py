# hh_bot/db/models/__init__.py

# Импорт всех моделей
from .models.user import User, SearchFilter, LLMSettings
from .models.vacancy import Vacancy, UserVacancyStatus
from .models.documents import GeneratedDocument

# Импорт перечислений из enums.py для обратной совместимости
# (раньше они были в models.py, теперь в отдельном файле)
from ..enums import (
    UserVacancyStatusEnum,
    EmploymentTypeEnum,
    ExperienceEnum,
    DocumentTypeEnum
)

# Экспорт всех сущностей для импорта через hh_bot.db.models
__all__ = [
    # Модели
    "User",
    "SearchFilter",
    "LLMSettings",
    "Vacancy",
    "UserVacancyStatus",
    "GeneratedDocument",
    
    # Перечисления
    "UserVacancyStatusEnum",
    "EmploymentTypeEnum",
    "ExperienceEnum",
    "DocumentTypeEnum",
]