# hh_bot/handlers/__init__.py

# Этот файл делает из 'handlers' пакет и экспортирует его модули
from . import user
from . import vacancies  # <-- ИМЕННО ЭТА СТРОКА ДОЛЖНА БЫТЬ ТАК
from . import settings
from .search_settings import search_settings_router, SearchSettingsStates