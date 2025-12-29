from aiogram import Router

# Создаем единый роутер для всех хэндлеров настроек
search_settings_router = Router(name="search_settings")

# Импортируем состояния для экспорта
from .states import SearchSettingsStates

# Импортируем и регистрируем хэндлеры
from . import handlers_start
from . import handlers_steps
from . import handlers_final

# Вызываем функции регистрации, чтобы "повесить" хэндлеры на роутер
handlers_start.register_start_handlers(search_settings_router)
handlers_steps.register_steps_handlers(search_settings_router)
handlers_final.register_final_handlers(search_settings_router)

# Экспортируем роутер и состояния для использования в основном приложении
__all__ = ["search_settings_router", "SearchSettingsStates"]