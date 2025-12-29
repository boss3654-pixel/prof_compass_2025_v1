import pytest
import pytest_asyncio
from unittest.mock import patch
import logging

from hh_bot.services.llm_service import generate_resume, generate_cover_letter

# Тестовые данные
VACANCY_INFO = {
    "title": "Python Developer",
    "company": "TechCorp"
}

USER_PROFILE = {
    "full_name": "Иван Иванов",
    "base_resume": "5 лет опыта разработки на Python"
}

LLM_SETTINGS = {
    "model": "gpt-4",
    "temperature": 0.7
}

@pytest.mark.asyncio
async def test_generate_resume_success():
    """Тест успешной генерации резюме"""
    resume = await generate_resume(VACANCY_INFO, USER_PROFILE, LLM_SETTINGS)
    
    # Проверка содержимого
    assert "Python Developer" in resume
    assert "TechCorp" in resume
    assert "Иван Иванов" in resume
    assert "5 лет опыта разработки на Python" in resume
    
    # ИСПРАВЛЕНО: Проверка полного заголовка вместо части
    assert "Адаптированное резюме для вакансии \"Python Developer\" в компании \"TechCorp\"" in resume
    assert "<b>Кандидат:</b>" in resume

@pytest.mark.asyncio
async def test_generate_resume_default_values():
    """Тест генерации резюме с умолчаниями при отсутствии данных"""
    resume = await generate_resume({}, {}, {})
    
    # Проверка значений по умолчанию
    assert "Не указана" in resume
    assert "Кандидат" in resume
    assert "Не указан" in resume

@pytest.mark.asyncio
async def test_generate_cover_letter_success():
    """Тест успешной генерации сопроводительного письма"""
    cover_letter = await generate_cover_letter(VACANCY_INFO, USER_PROFILE, LLM_SETTINGS)
    
    # Проверка содержимого
    assert "Python Developer" in cover_letter
    assert "TechCorp" in cover_letter
    assert "Иван Иванов" in cover_letter
    
    # Проверка форматирования
    assert "<b>Сопроводительное письмо</b>" in cover_letter
    assert "Уважаемый рекрутер компании" in cover_letter

@pytest.mark.asyncio
async def test_generate_cover_letter_default_values():
    """Тест генерации сопроводительного письма с умолчаниями при отсутствии данных"""
    cover_letter = await generate_cover_letter({}, {}, {})
    
    # Проверка значений по умолчанию
    assert "Не указана" in cover_letter
    assert "Кандидат" in cover_letter

@pytest.mark.asyncio
async def test_logging_for_resume(caplog):
    """Тест логгирования при генерации резюме"""
    caplog.set_level(logging.WARNING)
    
    await generate_resume(VACANCY_INFO, USER_PROFILE, LLM_SETTINGS)
    
    # Проверка наличия предупреждения в логах
    assert any("Используется ЗАГЛУШКА для генерации резюме!" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_logging_for_cover_letter(caplog):
    """Тест логгирования при генерации сопроводительного письма"""
    caplog.set_level(logging.WARNING)
    
    await generate_cover_letter(VACANCY_INFO, USER_PROFILE, LLM_SETTINGS)
    
    # Проверка наличия предупреждения в логах
    assert any("Используется ЗАГЛУШКА для генерации сопроводительного письма!" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_full_integration():
    """Тест полной интеграции с реалистичными данными"""
    # Данные из реального сценария
    real_vacancy = {
        "title": "Senior Data Scientist",
        "company": "AI Solutions Inc",
        "requirements": "Experience with ML frameworks"
    }
    
    real_user = {
        "full_name": "Мария Петрова",
        "base_resume": "Кандидат наук, 8 лет в machine learning",
        "skills": ["Python", "TensorFlow", "PyTorch"]
    }
    
    # Генерация резюме
    resume = await generate_resume(real_vacancy, real_user, {})
    
    # Генерация сопроводительного письма
    cover_letter = await generate_cover_letter(real_vacancy, real_user, {})
    
    # Проверка результатов
    assert "Senior Data Scientist" in resume
    assert "AI Solutions Inc" in resume
    assert "Мария Петрова" in resume
    assert "Кандидат наук, 8 лет в machine learning" in resume
    
    assert "Senior Data Scientist" in cover_letter
    assert "AI Solutions Inc" in cover_letter
    assert "Мария Петрова" in cover_letter
    assert "опыт отлично соответствует" in cover_letter