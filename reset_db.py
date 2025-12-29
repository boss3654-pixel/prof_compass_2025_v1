# reset_db.py
import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from hh_bot.utils.config import DATABASE_URL  # <--- ПРАВИЛЬНЫЙ ИМПОРТ

# --- Загрузка переменных окружения ---
load_dotenv()

# --- Получение URL ---
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ОШИБКА: DATABASE_URL не найдена в .env")
    exit(1)

print(f"Подключаюсь к базе данных для очистки...")

try:
    # Создаем движок SQLAlchemy
    engine = create_engine(db_url)

    with engine.connect() as connection:
        # Выполняем команды для очистки схемы
        connection.execute(text("DROP SCHEMA public CASCADE;"))
        connection.execute(text("CREATE SCHEMA public;"))

    print("База данных успешно очищена.")

except Exception as e:
    print(f"Произошла ошибка при очистке базы данных: {e}")
