import pytest
from unittest.mock import MagicMock
from typing import cast  # <-- 1. Добавляем импорт cast

# ИСПРАВЛЕНИЕ: Импортируем функции из правильного файла - formatting.py
from hh_bot.services.scheduler.jobs.formatting import format_salary, format_digest_message
# ИСПРАВЛЕНИЕ: Импортируем саму модель Vacancy для использования в cast
from hh_bot.db.models import Vacancy

# Тесты для format_salary
@pytest.mark.parametrize("salary_data, expected", [
    (None, "Не указана"),
    ({}, "По договорённости"),
    ({'from': 100000}, "от 100000"),
    ({'to': 150000}, "до 150000"),
    ({'from': 100000, 'to': 150000}, "от 100000 до 150000"),
    ({'from': 100000, 'currency': 'RUR'}, "от 100000 RUR"),
    ({'to': 150000, 'currency': 'USD'}, "до 150000 USD"),
    ({'from': 100000, 'to': 150000, 'currency': 'EUR'}, "от 100000 до 150000 EUR"),
])
def test_format_salary(salary_data, expected):
    assert format_salary(salary_data) == expected

# Тесты для format_digest_message
def create_mock_vacancy(title="Python Developer", company="Test Company", link="https://hh.ru/vacancy/123"):
    """Вспомогательная функция для создания мок-вакансии"""
    vac = MagicMock()
    vac.title = title
    vac.company = company
    vac.link = link
    return vac

def test_format_digest_message_empty():
    """Тест для пустого списка вакансий"""
    assert format_digest_message([]) == "Новых вакансий по вашим фильтрам не найдено."

def test_format_digest_message_single_vacancy():
    """Тест для одной вакансии"""
    vac = create_mock_vacancy()
    vac_data = {'salary': {'from': 100000, 'currency': 'RUR'}}
    
    # 2. Используем cast, чтобы "обмануть" Pylance
    result = format_digest_message([(cast(Vacancy, vac), vac_data)])
    
    expected = (
        "🔔 *Новые вакансии для вас (1 шт.)*\n\n"
        "1. *Python Developer*\n"
        "📍 Компания: Test Company\n"
        "💰 Зарплата: от 100000 RUR\n"
        "🔗 [Смотреть вакансию](https://hh.ru/vacancy/123)\n\n"
        "Используйте команду /vacancies, чтобы увидеть все и сгенерировать отклик."
    )
    assert result == expected

def test_format_digest_message_multiple_vacancies():
    """Тест для нескольких вакансий"""
    vac1 = create_mock_vacancy(title="Python Developer", company="Company A")
    vac2 = create_mock_vacancy(title="Data Scientist", company="Company B", link="https://hh.ru/vacancy/456")
    
    vacancies = [
        (cast(Vacancy, vac1), {'salary': {'from': 100000, 'currency': 'RUR'}}), # <-- и здесь
        (cast(Vacancy, vac2), {'salary': {'to': 200000, 'currency': 'USD'}}) # <-- и здесь
    ]
    
    result = format_digest_message(vacancies)
    
    assert "2 шт." in result
    assert "*Python Developer*" in result
    assert "*Data Scientist*" in result
    assert "Company A" in result
    assert "Company B" in result
    assert "от 100000 RUR" in result
    assert "до 200000 USD" in result

def test_format_digest_message_no_salary():
    """Тест для вакансии без указания зарплаты"""
    vac = create_mock_vacancy()
    vac_data = {}  # Нет данных о зарплате
    
    result = format_digest_message([(cast(Vacancy, vac), vac_data)]) # <-- и здесь
    
    assert "💰 Зарплата: Не указана" in result