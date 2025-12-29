# hh_bot/handlers/vacancies/__init__.py

# Этот файл делает папку `vacancies` Python-пакетом
# и позволяет импортировать роутеры из подпапок.

from .search import search_router
from .saved import saved_router
from .actions import actions_router