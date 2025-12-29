"""Логика обработки данных для фоновых задач."""

from typing import Dict, Any

from ....db.models import SearchFilter
from .constants import CITY_MAP

def prepare_hh_filters(search_filters: SearchFilter) -> Dict[str, Any]:
    """
    Подготавливает словарь фильтров для запроса к API hh.ru
    на основе настроек пользователя.
    """
    city_id = None
    # ИСПРАВЛЕНО: Добавлен комментарий для Pylance
    if search_filters.city:  # type: ignore
        city_name = search_filters.city.lower() # type: ignore
        city_id = CITY_MAP.get(city_name)
        # Если город не найден, city_id будет None, что корректно обработает hh_service
    
    return {
        'position': search_filters.position,
        'city_id': city_id,
        'salary_min': search_filters.salary_min,
        'remote': search_filters.remote,
        'freshness_days': search_filters.freshness_days,
        # ИСПРАВЛЕНО: Добавлены комментарии для Pylance
        'employment': search_filters.employment.value if search_filters.employment else None, # type: ignore
        'experience': search_filters.experience.value if search_filters.experience else None, # type: ignore
    }