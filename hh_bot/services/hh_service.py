"""
Сервис для взаимодействия с API hh.ru.
"""
import aiohttp
import json  # <--- Добавлен для красивого вывода в лог

# Импортируем логгер из папки utils
from ..utils.logger import logger

async def fetch_vacancies(filters: dict) -> list[dict]:
    """
    Асинхронно получает вакансии с hh.ru на основе фильтров.

    Args:
        filters: Словарь с параметрами поиска (должность, город, зарплата и т.д.).

    Returns:
        Список словарей с информацией о вакансиях.
        Возвращает пустой список в случае ошибки.
    """
    # API hh.ru для поиска вакансий
    url = "https://api.hh.ru/vacancies"
    
    # Подготовка параметров для запроса
    params = {
        'text': filters.get('position', ''),
        'area': filters.get('city'), # Стало
        'salary': filters.get('salary_min'),
        'only_with_salary': 'true' if filters.get('salary_min') else 'false',
        'schedule': 'remote' if filters.get('remote') else None,
        'period': filters.get('freshness_days', 1),
        'employment': filters.get('employment'),
        'experience': filters.get('experience'),
        'per_page': 50 # Ограничиваем количество для одного запроса
    }
    
    # Убираем None значения из параметров, чтобы не сломать запрос
    params = {k: v for k, v in params.items() if v is not None}

    # --- ДОБАВЛЕНО: Логирование параметров запроса ---
    # json.dumps делает словарь читаемым, ensure_ascii=False сохраняет кириллицу
    logger.info(f"Отправляю запрос к hh.ru с параметрами: {json.dumps(params, ensure_ascii=False, indent=2)}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                # raise_for_status вызовет исключение для кодов 4xx/5xx
                response.raise_for_status()
                data = await response.json()
                
                # --- ИЗМЕНЕНО: Более подробное логирование ответа ---
                found_count = data.get('found', 0)
                items_count = len(data.get('items', []))
                logger.info(f"hh.ru вернул ответ. Найдено всего: {found_count}. Получено на странице: {items_count}.")
                
                return data.get('items', [])
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка при запросе к API hh.ru: {e}")
        return [] # Возвращаем пустой список в случае ошибки
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка при запросе к hh.ru: {e}")
        return []