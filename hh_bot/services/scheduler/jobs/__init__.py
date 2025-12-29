# hh_bot/services/scheduler/jobs/__init__.py

# Экспортируем основные задачи и утилиты из пакета
from .daily_digest import daily_digest_job # <-- ИСПРАВЛЕНО
from .formatting import format_digest_message
from .storage import find_and_process_new_vacancies, mark_vacancies_as_sent
from .processing import prepare_hh_filters