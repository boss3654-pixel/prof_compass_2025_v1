from hh_bot.db.models import Vacancy

def format_vacancy_for_user(vac: Vacancy) -> str:
    """Форматирует вакансию для отправки пользователю."""
    # ИСПРАВЛЕНИЕ: Добавляем # type: ignore, чтобы заставить Pylance замолчать
    # Код корректен, это ограничение анализатора.
    salary_text = f"от {vac.salary}" if vac.salary else "з/п не указана"  # type: ignore
    city_text = vac.city or "город не указан"
    
    return (
        f"🏢 <b>{vac.title}</b>\n"
        f"🏭 Компания: {vac.company}\n"
        f"💰 Зарплата: {salary_text}\n"
        f"📍 Город: {city_text}\n"
        f"🔗 <a href='{vac.link}'>Смотреть вакансию</a>\n"
    )