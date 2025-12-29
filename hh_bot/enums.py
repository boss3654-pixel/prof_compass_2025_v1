# hh_bot/enums.py
from enum import Enum as PyEnum

class UserVacancyStatusEnum(str, PyEnum):
    """Статусы вакансии для пользователя."""
    # Значения в верхнем регистре для консистентности и соответствия БД
    SENT = "SENT"
    VIEWED = "VIEWED"
    NOT_INTERESTED = "NOT_INTERESTED"

class EmploymentTypeEnum(str, PyEnum):
    """Типы занятости."""
    # ИСПРАВЛЕНО: Значения изменены на верхний регистр
    # для соответствия типу ENUM в PostgreSQL.
    FULL = "FULL"
    PART = "PART"
    INTERNSHIP = "INTERNSHIP"
    PROJECT = "PROJECT"

class ExperienceEnum(str, PyEnum):
    """Требуемый опыт работы."""
    # ВАЖНО: Регистр этих значений (camelCase) должен точно совпадать
    # с тем, что ожидает API hh.ru и как определено в вашей БД.
    # Не меняйте их без необходимости.
    NO_EXPERIENCE = "noExperience"
    BETWEEN_1_AND_3 = "between1And3"
    BETWEEN_3_AND_6 = "between3And6"
    MORE_THAN_6 = "moreThan6"

class DocumentTypeEnum(str, PyEnum):
    """Типы генерируемых документов."""
    # ВАЖНО: Регистр этих значений (lower_case) должен точно совпадать
    # с тем, как они определены в вашей БД.
    RESUME = "RESUME"
    COVER_LETTER = "COVER_LETTER"