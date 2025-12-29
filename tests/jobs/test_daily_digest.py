import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ПРАВИЛЬНЫЙ ИМПОРТ Base и моделей
from hh_bot.db.base import Base
from hh_bot.db.models import User, SearchFilter, Vacancy, UserVacancyStatus, UserVacancyStatusEnum
from hh_bot.services.scheduler.jobs import daily_digest_job
from hh_bot.services.scheduler.jobs.constants import CITY_MAP

# --- ФИКСТУРЫ ---

@pytest_asyncio.fixture(scope="function")
async def async_session_maker():
    """Создает асинхронную сессию для тестов."""
    # Используем in-memory SQLite базу данных для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield maker
    await engine.dispose()


@pytest.fixture
def mock_bot():
    """Создает мок для бота."""
    return AsyncMock()


@pytest.fixture
def mock_fetch_vacancies(mocker):
    """Создает мок для функции fetch_vacancies."""
    # Мокаем функцию именно в том модуле, где она вызывается
    return mocker.patch("hh_bot.services.scheduler.jobs.daily_digest.fetch_vacancies", new_callable=AsyncMock)


@pytest_asyncio.fixture
async def user_with_filter(async_session_maker):
    """Создает в БД пользователя с фильтром поиска."""
    async with async_session_maker() as session:
        # Создаем пользователя
        new_user = User(telegram_id="123", full_name="Test User")
        session.add(new_user)
        await session.flush()  # Получаем ID пользователя

        # Создаем для него фильтр
        new_filter = SearchFilter(
            user_id=new_user.id,
            position="Python",
            city="москва",
            salary_min=None,
            remote=False,
            freshness_days=1,
        )
        session.add(new_filter)
        await session.commit()
        
        # Возвращаем ID пользователя для использования в тестах
        return new_user.id


# --- ТЕСТЫ ---

@pytest.mark.asyncio
async def test_daily_digest_no_users(async_session_maker, mock_bot, mock_fetch_vacancies):
    """Тест: нет пользователей с фильтрами -> ничего не происходит."""
    await daily_digest_job(mock_bot, async_session_maker)
    mock_fetch_vacancies.assert_not_called()
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_daily_digest_no_new_vacancies(user_with_filter, async_session_maker, mock_bot, mock_fetch_vacancies):
    """Тест: пользователь есть, но новых вакансий нет -> сообщение не отправляется."""
    mock_fetch_vacancies.return_value = []
    await daily_digest_job(mock_bot, async_session_maker)
    mock_fetch_vacancies.assert_called_once()
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_daily_digest_success_one_new_vacancy(user_with_filter, async_session_maker, mock_bot, mock_fetch_vacancies):
    """Тест: успешный сценарий с одной новой вакансией."""
    api_response = [{
        'id': 'hh_vac_1',
        'name': 'Python Developer',
        'employer': {'name': 'Cool Company'},
        'salary': {'from': 150000, 'currency': 'RUR'},
        'alternate_url': 'http://hh.ru/vac/1',
        'published_at': datetime.now(timezone.utc).isoformat(),
    }]
    mock_fetch_vacancies.return_value = api_response

    await daily_digest_job(mock_bot, async_session_maker)

    mock_fetch_vacancies.assert_called_once_with({
        'position': 'Python',
        'city_id': CITY_MAP['москва'],
        'salary_min': None,
        'remote': False,
        'freshness_days': 1,
        'employment': None,
        'experience': None,
    })

    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args

    # Получаем реальный telegram_id пользователя из базы
    async with async_session_maker() as session:
        user = await session.get(User, user_with_filter)
        expected_chat_id = int(user.telegram_id)

    assert call_args.kwargs['chat_id'] == expected_chat_id
    assert "Python Developer" in call_args.kwargs['text']
    assert "Cool Company" in call_args.kwargs['text']

    # Проверяем, что вакансия и статус были сохранены в БД
    async with async_session_maker() as session:
        vac_obj = await session.scalar(
            select(Vacancy).where(Vacancy.hh_id == 'hh_vac_1')
        )
        assert vac_obj is not None
        assert vac_obj.title == "Python Developer"

        status = await session.scalar(
            select(UserVacancyStatus).where(
                and_(
                    UserVacancyStatus.user_id == user_with_filter,
                    UserVacancyStatus.vacancy_id == vac_obj.id
                )
            )
        )
        assert status is not None
        assert status.status == UserVacancyStatusEnum.SENT

@pytest.mark.asyncio
async def test_daily_digest_send_message_failure(user_with_filter, async_session_maker, mock_bot, mock_fetch_vacancies):
    """Тест: ошибка при отправке сообщения -> транзакция откатывается."""
    mock_fetch_vacancies.return_value = [{
        'id': 'hh_vac_fail',
        'name': 'Fail Vacancy',
        'employer': {'name': 'Fail Co'},
        'alternate_url': 'http://hh.ru/fail',
        'published_at': datetime.now(timezone.utc).isoformat(),
    }]
    mock_bot.send_message.side_effect = Exception("Bot API error")

    await daily_digest_job(mock_bot, async_session_maker)

    mock_bot.send_message.assert_called_once()
    
    # Проверяем, что из-за ошибки статус не был сохранен
    async with async_session_maker() as session:
        status = await session.scalar(
            select(UserVacancyStatus).where(
                UserVacancyStatus.user_id == user_with_filter
            )
        )
        assert status is None