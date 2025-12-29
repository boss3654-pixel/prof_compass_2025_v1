import sys
import os
from pathlib import Path
import asyncio
import logging
import urllib.parse
from dotenv import load_dotenv

# === Настройка логирования ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("bot")

# === Инициализация среды ===
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("✅ Windows event loop policy установлен")

load_dotenv()
logger.info("🚀 Запуск бота...")

# === Проверка конфигурации ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "").strip()

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
    "ASYNC_DATABASE_URL": ASYNC_DATABASE_URL,
}

missing_vars = [var for var, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    logger.critical(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
    logger.info("Проверьте файл .env и заполните недостающие значения")
    sys.exit(1)

# === Импорты проекта (после проверки конфигурации) ===
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from hh_bot.db.database import (
    create_db_engine_and_sessionmaker,
    dispose_engine,
    get_session_maker,
    get_db_engine,
)
from hh_bot.handlers import user, settings
from hh_bot.handlers.vacancies import search_router, saved_router
from hh_bot.handlers.errors import errors_router
from hh_bot.middlewares import DbSessionMiddleware

# ИСПРАВЛЕНИЕ: Импортируем только новые, правильные функции
from hh_bot.services.scheduler import setup_scheduler, shutdown_scheduler

# УДАЛЕНО: Этот вызов был здесь ошибочно. Он вызывался до создания переменных `bot` и `async_session_maker`.
# setup_scheduler(bot=bot, async_session_maker=async_session_maker)


async def check_db_connection(url: str) -> bool:
    """Проверяет подключение к PostgreSQL базе данных"""
    if not url.startswith("postgresql+asyncpg://"):
        return True  # Не проверяем не-PostgreSQL подключения

    try:
        import psycopg2
    except ImportError:
        logger.warning("⚠️ psycopg2 не установлен. Пропускаю проверку подключения")
        return True  # Продолжаем работу без проверки

    try:
        # Преобразуем async URL в sync для проверки
        sync_url = url.replace("postgresql+asyncpg://", "postgresql://")
        parsed = urllib.parse.urlparse(sync_url)
        
        conn_params = {
            "dbname": parsed.path[1:] if parsed.path else "",
            "user": parsed.username or "",
            "password": parsed.password or "",
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "connect_timeout": 10,
            "application_name": "prof_compass_bot",
        }
        
        # Удаляем пустые параметры
        conn_params = {k: v for k, v in conn_params.items() if v}
        
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        logger.info("✅ Подключение к PostgreSQL успешно")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Ошибка подключения к БД: {str(e)}")
        return False


async def init_database(async_db_url: str):
    """Инициализирует базу данных с аварийным переходом на SQLite"""
    # Проверяем подключение только для PostgreSQL
    if async_db_url.startswith("postgresql+asyncpg://"):
        connection_ok = await check_db_connection(async_db_url)
        if not connection_ok:
            logger.warning("⚠️ Переключение на SQLite из-за проблем с PostgreSQL")

    # Аварийный переход на SQLite при проблемах или для разработки
    if not async_db_url.startswith("postgresql+asyncpg://") or "localhost" in async_db_url.lower():
        if not async_db_url.startswith("sqlite"):
            logger.warning("⚠️ Используется локальная БД. Переключаюсь на SQLite")
            sqlite_path = Path.cwd() / "data" / "bot_dev.db"
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            async_db_url = f"sqlite+aiosqlite:///{sqlite_path.as_posix()}"

    return create_db_engine_and_sessionmaker(async_db_url)


async def health_check(bot: Bot) -> bool:
    """Проверяет работоспособность бота"""
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот активен: @{bot_info.username} (ID: {bot_info.id})")
        return True
    except TelegramAPIError as e:
        logger.error(f"❌ Ошибка Telegram API: {str(e)}")
        logger.error("Проверьте правильность TELEGRAM_BOT_TOKEN в файле .env")
        return False


async def main():
    """Основная точка входа приложения"""
    try:
        # === Инициализация базы данных ===
        await init_database(ASYNC_DATABASE_URL)
        session_maker = get_session_maker()
        engine = get_db_engine()
        
        if not session_maker or not engine:
            raise RuntimeError("Не удалось инициализировать базу данных")

        # === Инициализация бота ===
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        if not await health_check(bot):
            return

        # === Настройка диспетчера ===
        dp = Dispatcher()
        dp.update.middleware(DbSessionMiddleware(session_pool=session_maker))
        
        # === Регистрация роутеров ===
        routers = [
            user.router,
            search_router,
            settings.router,
            saved_router,
            errors_router,
        ]
        
        for router in routers:
            dp.include_router(router)
            logger.debug(f"✅ Подключен роутер: {router.name or router.__class__.__name__}")

        # ИСПРАВЛЕНИЕ: Выводим количество роутеров после цикла
        logger.info(f"✅ Зарегистрировано роутеров: {len(routers)}")

        # === Запуск сервисов ===
        # ИСПРАВЛЕНИЕ: Вызываем setup_scheduler с нужными аргументами в правильном месте
        setup_scheduler(bot=bot, async_session_maker=session_maker)
        logger.info("✅ Планировщик задач запущен")

        # === Запуск поллинга ===
        logger.info("🚀 Бот успешно запущен! Отправьте /start для начала работы")
        await dp.start_polling(bot) # type: ignore

    except (KeyboardInterrupt, SystemExit):
        logger.info("✋ Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {str(e)}")
        raise
    finally:
        # === Корректное завершение работы ===
        try:
            shutdown_scheduler()
            logger.info("✅ Планировщик остановлен")
            
            if 'bot' in locals() and bot.session:
                await bot.session.close()
                logger.info("✅ Сессия бота закрыта")
            
            await dispose_engine()
            logger.info("✅ Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"⚠️ Ошибка при завершении работы: {str(e)}")
        
        logger.info("🛑 Работа бота завершена")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"❌ Фатальная ошибка при запуске: {str(e)}")
        sys.exit(1)