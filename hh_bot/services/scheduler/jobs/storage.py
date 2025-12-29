"""Операции с базой данных (хранилищем) для фоновых задач."""

import logging
from datetime import datetime, timezone
from typing import List, Tuple, Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# ИСПРАВЛЕНО: количество точек в импорте
from ....db.models import User, Vacancy, UserVacancyStatus, UserVacancyStatusEnum
# ИСПРАВЛЕНО: количество точек в импорте
from ....utils.logger import logger


def _format_salary_for_db(salary_data: Optional[dict]) -> Optional[str]:
    """
    Вспомогательная функция для форматирования зарплаты в строку для хранения в БД.
    Это предотвращает потерю информации (например, о верхней границе зарплаты).
    """
    if not salary_data or not isinstance(salary_data, dict):
        return None

    salary_from = salary_data.get('from')
    salary_to = salary_data.get('to')
    currency = salary_data.get('currency', '')

    # Формируем строку в зависимости от доступных данных
    if salary_from and salary_to:
        return f"{salary_from} - {salary_to} {currency}".strip()
    elif salary_from:
        return f"от {salary_from} {currency}".strip()
    elif salary_to:
        return f"до {salary_to} {currency}".strip()
    
    return None


async def get_users_with_filters(async_session_maker: async_sessionmaker[AsyncSession]) -> List[User]:
    """
    Получает всех пользователей, у которых есть хотя бы один фильтр поиска.
    
    ИСПРАВЛЕНИЕ: Явно преобразуем результат запроса в list, чтобы соответствовать
    аннотации возвращаемого типа List[User] и избежать предупреждений Pylance.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.search_filters.has())
        )
        # БЫЛО: return result.scalars().all()
        # СТАЛО:
        return list(result.scalars().all())


async def find_and_process_new_vacancies(
    user_session: AsyncSession,
    user_id: int,
    raw_vacancies: List[Dict[str, Any]]
) -> List[Tuple[Vacancy, Dict[str, Any]]]:
    """
    Находит новые вакансии для пользователя, которых ему еще не отправляли.
    Создает новые записи вакансий в БД.
    """
    if not raw_vacancies:
        return []

    hh_ids_to_process = {v['id'] for v in raw_vacancies}

    # 1. Найти все существующие вакансии из списка
    existing_vacancies_result = await user_session.execute(
        select(Vacancy).where(Vacancy.hh_id.in_(hh_ids_to_process))
    )
    existing_vacancies_map = {v.hh_id: v for v in existing_vacancies_result.scalars().all()}

    # 2. Найти ID вакансий, уже отправленных пользователю
    sent_vacancies_result = await user_session.execute(
        select(UserVacancyStatus.vacancy_id).where(
            UserVacancyStatus.user_id == user_id,
            UserVacancyStatus.vacancy_id.in_(
                select(Vacancy.id).where(Vacancy.hh_id.in_(hh_ids_to_process))
            )
        )
    )
    sent_vacancy_ids = {row[0] for row in sent_vacancies_result.all()}

    new_vacancies_for_user: List[Tuple[Vacancy, Dict[str, Any]]] = []

    for vac_data in raw_vacancies:
        vacancy_obj = existing_vacancies_map.get(vac_data['id'])

        if not vacancy_obj:
            # Создаем новую вакансию, если ее нет в БД
            
            # ИСПРАВЛЕНИЕ: Добавлен блок try-except для надежности парсинга даты.
            # Если API вернет некорректный формат, задача не упадет.
            published_at_dt = None
            try:
                published_at_str = vac_data.get('published_at')
                if published_at_str:
                    # Преобразуем в UTC и сохраняем как "наивное" время, 
                    # т.к. колонка в БД без таймзоны.
                    dt_with_tz = datetime.fromisoformat(published_at_str)
                    published_at_dt = dt_with_tz.astimezone(timezone.utc).replace(tzinfo=None)
            except (ValueError, TypeError) as e:
                logger.warning(f"Не удалось распарсить дату для вакансии {vac_data.get('id')}: {e}")

            # ИСПРАВЛЕНИЕ: Используем вспомогательную функцию для корректного форматирования зарплаты.
            # Это сохраняет больше информации (верхнюю границу, валюту).
            salary_str = _format_salary_for_db(vac_data.get('salary'))

            vacancy_obj = Vacancy(
                hh_id=vac_data['id'],
                title=vac_data.get('name'),
                company=vac_data.get('employer', {}).get('name'),
                salary=salary_str, # Используем отформатированную строку
                link=vac_data.get('alternate_url'),
                description_snippet=vac_data.get('snippet', {}).get('responsibility', ''),
                published_at=published_at_dt,
            )
            user_session.add(vacancy_obj)
            await user_session.flush() # Получаем ID для новой вакансии

        # Проверяем, отправляли ли мы эту вакансию пользователю
        if vacancy_obj.id not in sent_vacancy_ids:
            new_vacancies_for_user.append((vacancy_obj, vac_data))
            
    return new_vacancies_for_user


async def mark_vacancies_as_sent(
    user_session: AsyncSession,
    user_id: int,
    vacancies_to_mark: List[Vacancy]
):
    """
    Помечает список вакансий как отправленные для пользователя.
    
    ПРИМЕЧАНИЕ: Для большого количества вакансий (сотни) было бы эффективнее
    использовать `session.bulk_insert_mappings`, но для типичной подборки (5-10 шт.)
    этот подход прост и достаточно быстр.
    """
    for vac in vacancies_to_mark:
        user_session.add(UserVacancyStatus(
            user_id=user_id,
            vacancy_id=vac.id,
            status=UserVacancyStatusEnum.SENT
        ))
    # Commit/rollback должен обрабатываться вызывающим кодом