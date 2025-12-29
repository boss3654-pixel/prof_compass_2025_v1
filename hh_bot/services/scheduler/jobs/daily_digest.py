"""
Главная логика фоновой задачи ежедневной рассылки.
Этот файл является оркестратором, вызывающим другие модули.
"""
import logging
from typing import List, Tuple

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from hh_bot.services.hh_service import fetch_vacancies
from hh_bot.utils.logger import logger

# Локальные импорты из нашей новой структуры
from .constants import DIGEST_VACANCY_LIMIT
from .storage import find_and_process_new_vacancies, mark_vacancies_as_sent
from .processing import prepare_hh_filters
from .formatting import format_digest_message
from ....db.models import User, SearchFilter


async def daily_digest_job(
    bot: Bot,
    async_session_maker: async_sessionmaker[AsyncSession]
):
    """
    Фоновая задача для ежедневной рассылки вакансий.
    """
    logger.info("Запуск ежедневной рассылки вакансий.")
    
    try:
        # 1. Получаем пользователей и их фильтры в ОДНОЙ сессии
        users_data: List[Tuple[User, SearchFilter]] = []
        async with async_session_maker() as session:
            # Используем join, чтобы сразу получить и пользователя, и его фильтры
            stmt = select(User, SearchFilter).join(SearchFilter).where(SearchFilter.user_id == User.id)
            result = await session.execute(stmt)
            # Pylance ругается на тип, но в runtime это работает корректно.
            # Row[User, SearchFilter] при итерации распаковывается в (User, SearchFilter).
            users_data = result.all() # type: ignore

        if not users_data:
            logger.info("Нет пользователей с настроенными фильтрами. Рассылка не требуется.")
            return

        logger.info(f"Найдено {len(users_data)} пользователей для рассылки.")

        # 2. Проходим по собранным данным, создавая НОВУЮ сессию для каждого пользователя
        for user, search_filters in users_data:
            async with async_session_maker() as user_session:
                try:
                    logger.info(f"Обработка пользователя {user.full_name} (ID: {user.telegram_id})")
                    
                    # 1. Подготовка фильтров для HH, используя уже загруженный объект
                    filters_dict = prepare_hh_filters(search_filters)
                    if search_filters.city and not filters_dict.get('city_id'): # type: ignore
                         logger.warning(f"Город '{search_filters.city}' не найден в CITY_MAP для пользователя {user.telegram_id}.") # type: ignore

                    # 2. Получение вакансий из hh.ru
                    raw_vacancies = await fetch_vacancies(filters_dict)
                    
                    if not raw_vacancies:
                        logger.info(f"Для пользователя {user.telegram_id} не найдено вакансий.") # type: ignore
                        continue

                    # 3. Поиск и обработка новых вакансий
                    new_vacancies = await find_and_process_new_vacancies(
                        user_session, user.id, raw_vacancies # type: ignore
                    )

                    # 4. Отправка подборки пользователю
                    if new_vacancies:
                        vacancies_to_send = new_vacancies[:DIGEST_VACANCY_LIMIT]
                        digest_text = format_digest_message(vacancies_to_send)
                        
                        # СНАЧАЛА отправляем сообщение
                        await bot.send_message(
                            chat_id=int(user.telegram_id), # type: ignore
                            text=digest_text, 
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                        logger.info(f"Отправлена подборка из {len(vacancies_to_send)} вакансий пользователю {user.telegram_id}") # type: ignore
                        
                        # ТОЛЬКО ПОСЛЕ УСПЕШНОЙ ОТПРАВКИ помечаем вакансии как отправленные
                        all_new_vacancy_objects = [v for v, _ in new_vacancies]
                        await mark_vacancies_as_sent(user_session, user.id, all_new_vacancy_objects) # type: ignore
                        
                        # И коммитим изменения
                        await user_session.commit()
                except Exception as e:
                    logger.error(f"Не удалось обработать пользователя {user.telegram_id}: {e}", exc_info=True) # type: ignore
                    await user_session.rollback()

        logger.info("Ежедневная рассылка завершена.")

    except Exception as e:
        logger.critical(f"Критическая ошибка в процессе ежедневной рассылки: {e}", exc_info=True)