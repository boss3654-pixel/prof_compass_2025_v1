"""Утилиты для форматирования текста сообщений."""

from typing import Dict, List, Tuple, Any, Optional # ИСПРАВЛЕНО: добавлен Optional

# ИСПРАВЛЕНО: количество точек в импорте
from ....db.models import Vacancy

def format_salary(salary_obj: Optional[Dict[str, Any]]) -> str:
    """
    Форматирует объект зарплаты от hh.ru в читаемую строку.
    
    - None -> "Не указана" (данных о зарплате нет вообще)
    - {} -> "По договорённости" (данные есть, но пустые)
    """
    # ИСПРАВЛЕНИЕ: Проверяем именно на None, чтобы пустой словарь {} обрабатывался как "По договорённости"
    if salary_obj is None:
        return "Не указана"
    
    parts = []
    if salary_obj.get('from'):
        parts.append(f"от {salary_obj['from']}")
    if salary_obj.get('to'):
        parts.append(f"до {salary_obj['to']}")
    
    if not parts:
        # Эта ветка сработает для {} или для словаря без 'from'/'to'
        return "По договорённости"
        
    currency = salary_obj.get('currency', '')
    if currency:
        parts.append(currency.upper())
        
    return " ".join(parts)

def format_digest_message(new_vacancies: List[Tuple[Vacancy, Dict[str, Any]]]) -> str:
    """
    Форматирует полный текст дайджеста для пользователя.
    
    Args:
        new_vacancies: Список кортежей (объект Vacancy, сырые данные с hh.ru).
    
    Returns:
        Готовый текст для отправки.
    """
    if not new_vacancies:
        return "Новых вакансий по вашим фильтрам не найдено."

    digest_text = f"🔔 *Новые вакансии для вас ({len(new_vacancies)} шт.)*\n\n"
    
    for i, (vac, vac_data) in enumerate(new_vacancies):
        salary_text = format_salary(vac_data.get('salary'))

        digest_text += (
            f"{i+1}. *{vac.title}*\n"
            f"📍 Компания: {vac.company}\n"
            f"💰 Зарплата: {salary_text}\n"
            f"🔗 [Смотреть вакансию]({vac.link})\n\n"
        )
    
    digest_text += "Используйте команду /vacancies, чтобы увидеть все и сгенерировать отклик."
    return digest_text