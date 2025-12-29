import pytest
from hh_bot.db.models import Vacancy
from hh_bot.services.scheduler.utils import format_vacancy_for_user

@pytest.fixture
def sample_vacancy_full():
    """Фикстура с вакансией, у которой есть все данные."""
    return Vacancy(
        id=1,
        title="Python Developer",
        company="Super IT Company",
        salary="200000",
        city="Санкт-Петербург",
        link="https://hh.ru/vacancy/12345"
    )

@pytest.fixture
def sample_vacancy_empty():
    """Фикстура с вакансией, у которой нет зарплаты и города."""
    return Vacancy(
        id=2,
        title="Junior Tester",
        company="Another Co",
        salary=None,
        city=None,
        link="https://hh.ru/vacancy/67890"
    )

def test_format_vacancy_for_user_with_all_data(sample_vacancy_full):
    """
    Тест форматирования вакансии, когда все поля заполнены.
    """
    formatted_text = format_vacancy_for_user(sample_vacancy_full)

    # Проверяем наличие всех ключевых элементов
    assert "<b>Python Developer</b>" in formatted_text
    assert "Super IT Company" in formatted_text
    assert "от 200000" in formatted_text
    assert "Санкт-Петербург" in formatted_text
    assert "<a href='https://hh.ru/vacancy/12345'>Смотреть вакансию</a>" in formatted_text

def test_format_vacancy_for_user_with_missing_data(sample_vacancy_empty):
    """
    Тест форматирования вакансии, когда зарплата и город отсутствуют.
    """
    formatted_text = format_vacancy_for_user(sample_vacancy_empty)

    # Проверяем, что используются значения по умолчанию
    assert "<b>Junior Tester</b>" in formatted_text
    assert "Another Co" in formatted_text
    assert "з/п не указана" in formatted_text
    assert "город не указан" in formatted_text
    assert "<a href='https://hh.ru/vacancy/67890'>Смотреть вакансию</a>" in formatted_text

def test_format_vacancy_for_user_with_empty_strings():
    """
    Тест форматирования вакансии, когда зарплата и город - пустые строки.
    """
    vacancy_empty_strings = Vacancy(
        id=3,
        title="Data Scientist",
        company="Data Co",
        salary="",
        city="",
        link="https://hh.ru/vacancy/11111"
    )
    formatted_text = format_vacancy_for_user(vacancy_empty_strings)

    # Пустая строка ('') в Python является falsy, поэтому должен сработать тот же механизм,
    # что и для None
    assert "з/п не указана" in formatted_text
    assert "город не указан" in formatted_text