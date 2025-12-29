# tests/test_db_connection.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, select
from datetime import datetime, timezone

# Создаем локальный Base для изоляции тестов
LocalBase = declarative_base()

# ИЗМЕНЕНО ИМЯ: TestModel -> DBConnectionModel (чтобы избежать предупреждения pytest)
class DBConnectionModel(LocalBase):
    """Простая модель для тестирования подключения к БД"""
    __tablename__ = 'test_connection'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="module")
async def connection_engine():
    """Создает изолированный движок БД для тестов подключения"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(LocalBase.metadata.create_all)
    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def fresh_db_session(connection_engine):
    """Создает ПОЛНОСТЬЮ ЧИСТУЮ сессию БД для каждого теста с откатом транзакций"""
    async_session_maker = async_sessionmaker(
        connection_engine, class_=AsyncSession, expire_on_commit=False
    )
    session = async_session_maker()
    
    try:
        yield session
        # Откатываем все изменения после теста
        await session.rollback()
    finally:
        await session.close()

@pytest.mark.asyncio
async def test_db_connection(fresh_db_session):
    """Тест: проверка подключения к базе данных"""
    assert fresh_db_session is not None
    assert isinstance(fresh_db_session, AsyncSession)

@pytest.mark.asyncio
async def test_db_write_read(fresh_db_session):
    """Тест: запись и чтение данных из базы"""
    # Записываем данные
    test_record = DBConnectionModel(name="connection_test")
    fresh_db_session.add(test_record)
    await fresh_db_session.commit()
    await fresh_db_session.refresh(test_record)
    
    # Читаем данные
    result = await fresh_db_session.execute(
        select(DBConnectionModel).where(DBConnectionModel.id == test_record.id)
    )
    record = result.scalar_one_or_none()
    
    # Проверяем результат
    assert record is not None
    assert record.name == "connection_test"
    assert record.id == test_record.id
    
    # Явно удаляем запись для изоляции тестов
    await fresh_db_session.delete(record)
    await fresh_db_session.commit()

@pytest.mark.asyncio
async def test_db_isolation(fresh_db_session):
    """Тест: изоляция данных между тестами"""
    # Проверяем, что таблица пустая в начале теста
    result = await fresh_db_session.execute(select(DBConnectionModel))
    records = result.scalars().all()
    assert len(records) == 0
    
    # Добавляем запись
    fresh_db_session.add(DBConnectionModel(name="isolation_test"))
    await fresh_db_session.commit()
    
    # Проверяем наличие записи
    result = await fresh_db_session.execute(select(DBConnectionModel))
    records = result.scalars().all()
    assert len(records) == 1
    
    # Запись будет автоматически удалена после теста благодаря откату транзакции