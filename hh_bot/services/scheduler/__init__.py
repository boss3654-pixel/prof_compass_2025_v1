# Импортируем и экспортируем основные функции для удобного использования
from .service import setup_scheduler, shutdown_scheduler, scheduler # <-- ИСПРАВЛЕНО: start_scheduler -> setup_scheduler
from .config import set_bot_instance, set_session_maker, get_bot, get_session_maker

# Экспортируем для использования в других частях проекта
__all__ = [
    "set_bot_instance",
    "set_session_maker",
    "setup_scheduler", # <-- ИСПРАВЛЕНО: start_scheduler -> setup_scheduler
    "shutdown_scheduler",
    "scheduler",
    "get_bot",
    "get_session_maker"
]