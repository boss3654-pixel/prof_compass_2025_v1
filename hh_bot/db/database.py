# hh_bot/db/database.py
"""
Модуль для создания и управления подключением к базе данных.

Содержит функции для инициализации асинхронного движка SQLAlchemy
и создания таблиц в базе данных.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from typing import Tuple, Optional
from ..utils.logger import logger
import asyncio
from .base import Base  # Импортируем Base из нового файла

# Глобальные переменные для движка и фабрики сессий
async_engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

def get_db_engine() -> Optional[AsyncEngine]:
    """Возвращает глобальный экземпляр движка базы данных."""
    if async_engine is None:
        logger.error("Движок базы данных не инициализирован. Сначала вызовите create_db_engine_and_sessionmaker()")
    return async_engine

def get_session_maker() -> Optional[async_sessionmaker[AsyncSession]]:
    """Возвращает глобальную фабрику сессий."""
    if async_session_maker is None:
        logger.error("Фабрика сессий не инициализирована. Сначала вызовите create_db_engine_and_sessionmaker()")
    return async_session_maker

def create_db_engine_and_sessionmaker(
    async_db_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30
) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    Создает асинхронный движок базы данных и фабрику сессий.

    Args:
        async_db_url: URL для подключения к базе данных
        echo: Если True, все SQL-запросы будут выводиться в логи
        pool_size: Количество постоянных соединений в пуле
        max_overflow: Максимальное количество дополнительных соединений
        pool_timeout: Таймаут в секундах для получения соединения из пула

    Returns:
        tuple: (engine, session_maker) - движок базы данных и фабрика сессий
    """
    global async_engine, async_session_maker
    
    # Проверяем, был ли уже инициализирован движок
    if async_engine is not None:
        logger.warning("Движок базы данных уже инициализирован. Пересоздание...")
        # При пересоздании нужно закрыть старый движок
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(async_engine.dispose())
        except RuntimeError:
            # Если нет запущенного цикла событий, закрываем синхронно
            asyncio.run(async_engine.dispose())

    try:
        # Создаем асинхронный движок
        engine = create_async_engine(
            async_db_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=1800  # Пересоздание соединений каждые 30 минут
        )
        logger.info(f"✅ Движок базы данных успешно создан. Echo={'включен' if echo else 'отключен'}")

        # Создаем фабрику сессий
        session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        logger.info("✅ Фабрика сессий успешно создана")

        # Сохраняем глобальные ссылки
        async_engine = engine
        async_session_maker = session_maker

        return engine, session_maker
    except Exception as e:
        logger.critical(f"❌ Не удалось создать движок базы данных: {str(e)}")
        raise  # Пробрасываем исключение наверх для обработки в вызывающем коде

async def create_tables(engine: Optional[AsyncEngine] = None) -> None:
    """
    Асинхронно создает все таблицы, определенные в моделях.

    Args:
        engine: Движок базы данных. Если не указан, используется глобальный движок.
    """
    db_engine = engine or async_engine
    
    if db_engine is None:
        error_msg = "Движок базы данных не инициализирован. Сначала вызовите create_db_engine_and_sessionmaker()"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)

    try:
        async with db_engine.begin() as conn:
            # ЯВНЫЕ импорты вместо wildcard
            from hh_bot.db.models.user import User  # noqa: F401
            from hh_bot.db.models.vacancy import Vacancy, UserVacancyStatus  # noqa: F401
            from hh_bot.db.models.documents import GeneratedDocument  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Все таблицы в базе данных успешно созданы или уже существуют")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {str(e)}")
        raise

async def dispose_engine() -> None:
    """Закрывает все соединения и очищает ресурсы движка базы данных."""
    global async_engine, async_session_maker
    
    if async_engine is not None:
        await async_engine.dispose()
        logger.info("✅ Движок базы данных успешно закрыт")
    
    # Сбрасываем глобальные переменные
    async_engine = None
    async_session_maker = None