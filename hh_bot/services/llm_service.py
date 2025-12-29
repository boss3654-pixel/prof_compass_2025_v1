# hh_bot/services/llm_service.py

from ..utils.logger import logger


async def generate_resume(
    vacancy_info: dict, user_profile: dict, llm_settings: dict
) -> str:
    """
    ВРЕМЕННАЯ ЗАГЛУШКА.
    Генерирует шаблонный текст резюме на основе данных пользователя и вакансии.
    Замените этот код на реальный вызов API, когда будете готовы.
    """
    logger.warning("Используется ЗАГЛУШКА для генерации резюме! LLM не вызывается.")

    # Извлекаем данные для удобства
    vacancy_title = vacancy_info.get("title", "Не указана")
    company_name = vacancy_info.get("company", "Не указана")

    full_name = user_profile.get("full_name", "Кандидат")
    base_resume = user_profile.get("base_resume", "Не указан")

    # Формируем текст резюме, используя данные о вакансии
    resume_text = f"""
    <b>Адаптированное резюме для вакансии "{vacancy_title}" в компании "{company_name}"</b>

    <b>Кандидат:</b> {full_name}

    <b>Ключевой опыт:</b>
    {base_resume}

    <b>Обо мне:</b>
    Мой опыт и навыки отлично подходят для требований, указанных в вашей вакансии. Я уверен, что смогу стать ценным членом вашей команды.
    """

    return resume_text


async def generate_cover_letter(
    vacancy_info: dict, user_profile: dict, llm_settings: dict
) -> str:
    """
    ВРЕМЕННАЯ ЗАГЛУШКА для генерации сопроводительного письма.
    """
    logger.warning("Используется ЗАГЛУШКА для генерации сопроводительного письма!")

    vacancy_title = vacancy_info.get("title", "Не указана")
    company_name = vacancy_info.get("company", "Не указана")
    full_name = user_profile.get("full_name", "Кандидат")

    return f"""
    <b>Сопроводительное письмо</b>

    Уважаемый рекрутер компании "{company_name}",

    С большим интересом ознакомился с вашей вакансией на должность "{vacancy_title}" и уверен, что мой опыт отлично соответствует вашим требованиям.

    Буду рад подробно рассказать о своем опыте на собеседовании.

    С уважением,
    {full_name}
    """
