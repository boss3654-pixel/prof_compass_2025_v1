import os
from dotenv import load_dotenv, find_dotenv

# --- Загрузка переменных окружения ---
# find_dotenv() ищет .env файл в текущей и родительских директориях.
# Это делает запуск более надежным.
load_dotenv(find_dotenv())

# --- Получение переменных из .env файла ---
# Для Alembic (миграций) - синхронный драйвер
DATABASE_URL = os.getenv("DATABASE_URL")

# Для основного приложения (бота) - асинхронный драйвер
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

# Остальные переменные
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")


# --- Проверка наличия всех обязательных переменных ---
# Мы создаем словарь переменных, которые критически важны для запуска.
required_variables = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "DATABASE_URL": DATABASE_URL,  # Нужен для Alembic
    "ASYNC_DATABASE_URL": ASYNC_DATABASE_URL,  # Нужен для бота
}

# Находим все переменные, которые не были загружены (имеют значение None)
missing_variables = [name for name, value in required_variables.items() if not value]

# Если список отсутствующих переменных не пуст, выводим ошибку и выходим
if missing_variables:
    # Импортируем logger здесь, чтобы избежать циклических зависимостей
    from .logger import logger

    logger.critical(
        f"ОШИБКА: Отсутствуют следующие обязательные переменные окружения: {', '.join(missing_variables)}. "
        "Проверьте ваш файл .env и убедитесь, что все переменные установлены."
    )
    exit(1)


def get_config():
    """
    Возвращает словарь с конфигурацией приложения.
    """
    return {
        "DATABASE_URL": DATABASE_URL,
        "ASYNC_DATABASE_URL": ASYNC_DATABASE_URL,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "LLM_BASE_URL": LLM_BASE_URL,
        "LLM_API_KEY": LLM_API_KEY,
        "LLM_MODEL": LLM_MODEL,
    }
