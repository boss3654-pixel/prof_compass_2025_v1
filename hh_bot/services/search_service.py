import urllib.parse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from ..db.models import Vacancy, UserVacancyStatus, User
from ..utils.logger import logger
from ..enums import UserVacancyStatusEnum
from ..keyboards.inline_keyboards import get_vacancy_actions_keyboard
from .hh_service import fetch_vacancies


async def process_search_results(
    message,  # Объект сообщения для отправки ответов
    state,  # Объект состояния FSM
    session: AsyncSession,  # Сессия базы данных
    user: User,  # Объект пользователя из middleware
    filters_dict: dict,  # Словарь с фильтрами для поиска
):
    """
    Основная функция для обработки поиска вакансий.

    1. Выполняет запрос к API hh.ru.
    2. Обрабатывает результаты (проверяет наличие в БД, добавляет новые).
    3. Сохраняет все в базу данных.
    4. Отправляет результаты пользователю.

    Returns:
        bool: True в случае успеха, False в случае ошибки.
    """
    try:
        await message.answer(
            "🔍 Ищу вакансии по вашим параметрам, это может занять время..."
        )
        raw_vacancies = await fetch_vacancies(filters_dict)
    except Exception as e:
        logger.error(f"Ошибка при вызове сервиса поиска: {e}")
        # ИСПРАВЛЕНИЕ: Добавлен откат транзакции при ошибке API
        await session.rollback()
        await message.answer("❌ Произошла ошибка во время поиска. Попробуйте позже.")
        return False

    if not raw_vacancies:
        await message.answer(
            "По вашим критериям вакансий не найдено. Попробуйте изменить параметры."
        )
        return True  # Это не ошибка, просто нет результатов

    await message.answer(
        f"🎉 Найдено вакансий: {len(raw_vacancies)}. Сохраняю и показываю результаты..."
    )

    found_vacancies_to_show = []

    # ИСПРАВЛЕНИЕ: Добавлен общий try-except для обработки ошибок при работе с БД
    try:
        # Используем блок no_autoflush для безопасности
        with session.no_autoflush:
            for vac_data in raw_vacancies[:10]:  # Ограничиваем вывод 10 вакансиями
                # Проверяем, есть ли вакансия уже в БД
                existing_vac = await session.scalar(
                    select(Vacancy).where(Vacancy.hh_id == vac_data["id"])
                )

                vac_obj = existing_vac
                if not existing_vac:
                    published_at_str = vac_data.get("published_at")
                    published_at_dt = None
                    if published_at_str:
                        dt_with_tz = datetime.fromisoformat(published_at_str)
                        published_at_dt = dt_with_tz.astimezone(timezone.utc).replace(
                            tzinfo=None
                        )

                    salary_value = vac_data.get("salary", {}).get("from")
                    salary_str = str(salary_value) if salary_value is not None else None

                    # Получаем прямую ссылку на отклик, используем резервный вариант если нет
                    apply_url = vac_data.get("apply_url", vac_data.get("alternate_url"))

                    # Если новой вакансии нет в БД, добавляем ее
                    vac_obj = Vacancy(
                        hh_id=vac_data["id"],
                        title=vac_data.get("name"),
                        company=vac_data.get("employer", {}).get("name"),
                        salary=salary_str,
                        link=vac_data.get("alternate_url"),
                        apply_url=apply_url,
                        description_snippet=vac_data.get("snippet", {}).get(
                            "responsibility", ""
                        ),
                        published_at=published_at_dt,
                    )
                    session.add(vac_obj)
                    await session.flush()  # Получаем ID новой вакансии

                # Создаем связь между пользователем и вакансией
                user_vacancy_status = UserVacancyStatus(
                    user_id=user.id,
                    vacancy_id=vac_obj.id,  # type: ignore
                    status=UserVacancyStatusEnum.SENT.value,
                )
                session.add(user_vacancy_status)
                found_vacancies_to_show.append(vac_obj)

        # Сохраняем все в БД одним запросом
        await session.commit()

    except Exception as e:
        logger.error(f"Ошибка при сохранении вакансий в БД: {e}", exc_info=True)
        # ИСПРАВЛЕНИЕ: Добавлен откат транзакции при ошибке сохранения
        await session.rollback()
        await message.answer("💥 Произошла ошибка при сохранении результатов. Попробуйте позже.")
        return False

    # Отправляем результаты пользователю
    await message.answer("Вот что мне удалось найти:")
    for vac in found_vacancies_to_show:
        salary_text = f"от {vac.salary}" if vac.salary else "Не указана"

        # Безопасное форматирование URL для Markdown
        safe_link = urllib.parse.quote(vac.link, safe=':/?=&#') if vac.link else ""
        safe_apply_url = urllib.parse.quote(vac.apply_url or vac.link, safe=':/?=&#') if (vac.apply_url or vac.link) else ""

        # Формируем текст сообщения с правильным форматированием
        text = (
            f"🏢 *{vac.title}*\n"
            f"📍 Компания: {vac.company}\n"
            f"💰 Зарплата: {salary_text}\n"
            f"🔗 [Смотреть вакансию]({safe_link})\n"
            f"✅ [Откликнуться]({safe_apply_url})"
        )

        # Передаем безопасное значение для apply_url в клавиатуру
        keyboard = get_vacancy_actions_keyboard(vac.hh_id, vac.apply_url or vac.link)

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

    logger.info(
        f"Пользователь {user.id} (tg: {user.telegram_id}) завершил поиск. Найдено и сохранено: {len(found_vacancies_to_show)} вакансий."
    )
    return True