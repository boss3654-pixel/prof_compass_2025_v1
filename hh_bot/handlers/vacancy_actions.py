# hh_bot/handlers/vacancy_actions.py

from aiogram import Router

# Импортируем наши новые, специализированные роутеры
from . import document_generation, status_updates, confirmations

# Создаем главный роутер для действий с вакансиями
vacancy_actions_router = Router(name="vacancy_actions")

# Включаем в него более мелкие роутеры. Теперь вся логика разнесена по файлам.
vacancy_actions_router.include_router(document_generation.document_generation_router)
vacancy_actions_router.include_router(status_updates.status_updates_router)
vacancy_actions_router.include_router(confirmations.confirmation_router)