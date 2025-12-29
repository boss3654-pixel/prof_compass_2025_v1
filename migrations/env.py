import os
from dotenv import load_dotenv
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine # <-- engine_from_config был здесь, он не нужен

from alembic import context

# Загружаем переменные окружения из .env файла
load_dotenv()

# Это объект конфигурации Alembic, который предоставляет
# доступ к значениям внутри используемого .ini файла
config = context.config

# Настройка логирования Python
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем метаданные вашей модели сюда для поддержки 'autogenerate'
# ВАЖНО: импорт должен соответствовать вашей структуре проекта
from hh_bot.db.models import Base
target_metadata = Base.metadata

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в переменных окружения")

def run_migrations_offline() -> None:
    """Запуск миграций в 'офлайн' режиме."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в 'онлайн' режиме."""
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()