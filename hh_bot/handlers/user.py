# hh_bot/handlers/user.py

from aiogram import types, Router
from ..utils.logger import logger

# Импортируем наши новые роутеры
from .registration import registration_router
from .vacancy_actions import vacancy_actions_router
from .menu_handlers import menu_handlers_router

# Создаем главный роутер для пользователя
router = Router(name="main_user_router")

# Включаем в него все остальные роутеры
router.include_router(registration_router)
router.include_router(vacancy_actions_router)
router.include_router(menu_handlers_router)

# ВАЖНО: Глобальный обработчик неизвестных кнопок был УДАЛЕН отсюда.
# Он должен находиться в отдельном роутере (например, errors_router)
# и подключаться в main.py самым последним, чтобы не перехватывать
# обработчики из других роутеров.