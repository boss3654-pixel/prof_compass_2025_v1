import pytest
import pytest_asyncio
import logging
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import hh_bot.services.scheduler.service as service_module
from hh_bot.services.scheduler.service import setup_scheduler, shutdown_scheduler

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level(logging.INFO)
    logging.getLogger("hh_bot").setLevel(logging.INFO)
    yield

@pytest_asyncio.fixture(autouse=True)
async def reset_scheduler():
    """Сбрасывает состояние планировщика перед каждым тестом."""
    # Останавливаем текущий планировщик если он запущен
    if hasattr(service_module, 'scheduler') and service_module.scheduler.running:
        try:
            service_module.scheduler.shutdown(wait=False)
        except:
            pass
    
    # Создаем новый планировщик для каждого теста
    service_module.scheduler = AsyncIOScheduler()
    
    yield
    
    # Очищаем после теста
    if service_module.scheduler.running:
        try:
            service_module.scheduler.shutdown(wait=False)
        except:
            pass
    service_module.scheduler = AsyncIOScheduler()

@pytest.fixture
def mock_bot():
    """Мок для Telegram бота."""
    return AsyncMock()

@pytest.fixture
def mock_session_maker():
    """Мок для фабрики сессий SQLAlchemy."""
    return MagicMock()

@pytest.fixture
def mock_daily_digest_job():
    """Мок для функции ежедневной рассылки."""
    return AsyncMock()

def test_scheduler_initial_state():
    """Тест начального состояния планировщика."""
    assert service_module.scheduler.running is False
    assert len(service_module.scheduler.get_jobs()) == 0

@pytest.mark.asyncio
async def test_setup_scheduler_success(mock_bot, mock_session_maker, mock_daily_digest_job, caplog):
    """Тест успешной настройки планировщика."""
    with patch('hh_bot.services.scheduler.service.daily_digest_job', mock_daily_digest_job):
        setup_scheduler(mock_bot, mock_session_maker)
        
        # Проверяем, что планировщик запущен
        assert service_module.scheduler.running is True
        
        # Проверяем, что задача добавлена
        jobs = service_module.scheduler.get_jobs()
        assert len(jobs) == 1
        
        job = jobs[0]
        assert job.id == "daily_digest_job"
        assert job.name == "Ежедневная рассылка вакансий"
        
        # Проверяем триггер (9:00 каждый день)
        assert isinstance(job.trigger, CronTrigger)
        assert '9' in str(job.trigger) and '0' in str(job.trigger)
        
        # Проверяем аргументы задачи
        assert job.kwargs["bot"] is mock_bot
        assert job.kwargs["async_session_maker"] is mock_session_maker
        
        # Проверяем логирование
        assert "Планировщик задач запущен. Ежедневная рассылка назначена на 9:00 по МСК." in caplog.text

@pytest.mark.asyncio
async def test_shutdown_scheduler_success(caplog):
    """Тест успешной остановки планировщика."""
    # Запускаем планировщик
    service_module.scheduler.start()
    assert service_module.scheduler.running is True
    
    # ИСПРАВЛЕНИЕ: Вызываем как синхронную функцию
    shutdown_scheduler()
    
    # Даем планировщику время на обновление состояния
    await asyncio.sleep(0.1)
    
    # Проверяем, что планировщик остановлен
    assert service_module.scheduler.running is False
    
    # Проверяем логирование
    assert "Планировщик задач остановлен." in caplog.text

@pytest.mark.asyncio
async def test_setup_scheduler_replace_existing(mock_bot, mock_session_maker, mock_daily_digest_job):
    """Тест замены существующей задачи при повторной настройке."""
    with patch('hh_bot.services.scheduler.service.daily_digest_job', mock_daily_digest_job):
        # Настраиваем планировщик первый раз
        setup_scheduler(mock_bot, mock_session_maker)
        assert len(service_module.scheduler.get_jobs()) == 1
        
        # Останавливаем планировщик перед повторной настройкой
        if service_module.scheduler.running:
            service_module.scheduler.shutdown(wait=False)
        service_module.scheduler = AsyncIOScheduler()
        
        # Настраиваем планировщик второй раз
        setup_scheduler(mock_bot, mock_session_maker)
        
        # Проверяем, что количество задач не увеличилось (замена произошла)
        jobs = service_module.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "daily_digest_job"

@pytest.mark.asyncio
async def test_shutdown_scheduler_logs_info(caplog):
    """Тест логирования при остановке планировщика."""
    # Сначала запускаем планировщик
    service_module.scheduler.start()
    assert service_module.scheduler.running is True
    
    # ИСПРАВЛЕНИЕ: Вызываем как синхронную функцию и здесь тоже
    shutdown_scheduler()
    await asyncio.sleep(0.1)
    
    # Проверяем логи (регистронезависимая проверка)
    log_messages = [record.message for record in caplog.records]
    assert any("планировщик задач остановлен" in msg.lower() for msg in log_messages)

@pytest.mark.asyncio
async def test_setup_scheduler_logs_info(caplog, mock_bot, mock_session_maker, mock_daily_digest_job):
    """Тест логирования при настройке планировщика."""
    with patch('hh_bot.services.scheduler.service.daily_digest_job', mock_daily_digest_job):
        setup_scheduler(mock_bot, mock_session_maker)
        
        # Проверяем логи (регистронезависимая проверка)
        log_messages = [record.message for record in caplog.records]
        assert any("планировщик задач запущен" in msg.lower() and "ежедневная рассылка" in msg.lower() 
                   for msg in log_messages)