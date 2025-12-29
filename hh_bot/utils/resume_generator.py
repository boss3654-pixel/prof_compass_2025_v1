# hh_bot/utils/resume_generator.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.models import User, Vacancy
from ..utils.logger import logger

async def generate_resume_for_vacancy(vacancy_id: int, user_id: int, session: AsyncSession) -> str:
    """
    Генерирует текст резюме на основе данных пользователя и вакансии.
    """
    # Получаем данные пользователя
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("Пользователь не найден")

    # Получаем данные вакансии
    vacancy_result = await session.execute(select(Vacancy).where(Vacancy.hh_id == str(vacancy_id)))
    vacancy = vacancy_result.scalar_one_or_none()
    if not vacancy:
        raise ValueError("Вакансия не найдена")

    logger.info(f"Генерация резюме для пользователя {user.full_name} по вакансии '{vacancy.title}'")

    # --- ЛОГИКА ГЕНЕРАЦИИ РЕЗЮМЕ ---
    # Здесь вы можете использовать любую логику: шаблоны, AI и т.д.
    # Это простой пример конкатенации строк.
    
    resume_text = f"""
**Резюме на вакансию: {vacancy.title}**

**Кандидат:** {user.full_name}
**Город:** {user.city}
**Желаемая должность:** {user.desired_position}

**Ключевые навыки:**
{user.skills}

**Опыт:**
{user.base_resume}

---
*Сгенерировано PROF_COMPASS_2025 Bot*
    """
    
    return resume_text.strip()