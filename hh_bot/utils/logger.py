import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы получить уровень логирования, если он задан
load_dotenv()

# Получаем уровень логирования из переменной окружения, по умолчанию INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Настройка логгера ---
logging.basicConfig(
    level=getattr(logging, log_level), # Устанавливаем уровень динамически
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем корневой логгер, который будут использовать все модули
logger = logging.getLogger(__name__)