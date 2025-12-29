# hh_bot/utils/cover_letter_generator.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.models import User, Vacancy
from ..utils.logger import logger

async def generate_cover_letter_for_vacancy(vacancy_id: int, user_id: int, session: AsyncSession) -> str:
    """
    Генерирует текст сопроводительного письма на основе данных пользователя и вакансии.
    """
    # Получаем данные пользователя
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("Пользователь не найден")

    # Получаем данные вакансии
    vacancy_result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = vacancy_result.scalar_one_or_none()
    if not vacancy:
        raise ValueError("Вакансия не найдена")

    logger.info(f"Генерация письма для пользователя {user.full_name} по вакансии '{vacancy.title}'")

    # --- ЛОГИКА ГЕНЕРАЦИИ ПИСЬМА (с защитой от пустых полей) ---
    full_name = user.full_name or 'Не указано'
    city = user.city or 'Не указан'
    desired_position = user.desired_position or 'Не указана'
    skills = user.skills or 'Не указаны'
    base_resume = user.base_resume or 'Не указано'
    vacancy_title = vacancy.title or 'Название не указано'
    company_name = vacancy.company or 'Название компании не указано'

    cover_letter_text = f"""
Уважаемый HR-менеджер!

Меня заинтересовала ваша вакансия на позицию «{vacancy_title}» в компании «{company_name}».

Я обладаю опытом работы в {desired_position} и уверен(а), что мои навыки в {skills} будут полезны для вашей команды.

Мое резюме для более детального ознакомления:
{base_resume}

Буду благодарен(а) за возможность обсудить мое кандидатуру на собеседовании.

С уважением,
{full_name}
Город: {city}
---
*Сгенерировано PROF_COMPASS_2025 Bot*
    """
    
    return cover_letter_text.strip()