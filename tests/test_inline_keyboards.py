import pytest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from hh_bot.keyboards.inline_keyboards import (
    get_main_menu_keyboard,
    get_remote_keyboard,
    get_freshness_keyboard,
    get_employment_keyboard,
    get_experience_keyboard,
    get_employer_type_keyboard,
    get_save_cancel_keyboard,
    get_vacancy_actions_keyboard,
    get_apply_confirmation_keyboard
)

def test_get_main_menu_keyboard():
    """Тест главного меню."""
    keyboard = get_main_menu_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 3  # Три кнопки в отдельных строках
    assert buttons[0][0].text == "🔍 Найти вакансии"
    assert buttons[0][0].callback_data == "menu_search"
    assert buttons[1][0].text == "⚙️ Настройки"
    assert buttons[1][0].callback_data == "menu_settings"
    assert buttons[2][0].text == "📄 Мои резюме"
    assert buttons[2][0].callback_data == "menu_resumes"

def test_get_remote_keyboard():
    """Тест клавиатуры для выбора удаленной работы."""
    keyboard = get_remote_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 1  # Одна строка с двумя кнопками
    assert len(buttons[0]) == 2  # Две кнопки в строке
    assert buttons[0][0].text == "Да"
    assert buttons[0][0].callback_data == "setting_remote_yes"
    assert buttons[0][1].text == "Нет"
    assert buttons[0][1].callback_data == "setting_remote_no"

def test_get_freshness_keyboard():
    """Тест клавиатуры для выбора свежести вакансий."""
    keyboard = get_freshness_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 3  # Три кнопки в отдельных строках
    assert buttons[0][0].text == "За 1 день"
    assert buttons[0][0].callback_data == "setting_freshness_1"
    assert buttons[1][0].text == "За 3 дня"
    assert buttons[1][0].callback_data == "setting_freshness_3"
    assert buttons[2][0].text == "За 7 дней"
    assert buttons[2][0].callback_data == "setting_freshness_7"

def test_get_employment_keyboard():
    """Тест клавиатуры для выбора типа занятости."""
    keyboard = get_employment_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 4  # Четыре кнопки в отдельных строках
    texts = ["Полная занятость", "Частичная занятость", "Стажировка", "Проектная работа"]
    callbacks = [
        "setting_employment_full",
        "setting_employment_part",
        "setting_employment_internship",
        "setting_employment_project"
    ]
    
    for i, (text, callback) in enumerate(zip(texts, callbacks)):
        assert buttons[i][0].text == text
        assert buttons[i][0].callback_data == callback

def test_get_experience_keyboard():
    """Тест клавиатуры для выбора опыта работы."""
    keyboard = get_experience_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 4  # Четыре кнопки в отдельных строках
    texts = ["Нет опыта", "От 1 года до 3 лет", "От 3 до 6 лет", "Более 6 лет"]
    callbacks = [
        "setting_experience_noExperience",
        "setting_experience_between1And3",
        "setting_experience_between3And6",
        "setting_experience_moreThan6"
    ]
    
    for i, (text, callback) in enumerate(zip(texts, callbacks)):
        assert buttons[i][0].text == text
        assert buttons[i][0].callback_data == callback

def test_get_employer_type_keyboard():
    """Тест клавиатуры для выбора типа работодателя."""
    keyboard = get_employer_type_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 2  # Две кнопки в отдельных строках
    assert buttons[0][0].text == "Только прямые работодатели"
    assert buttons[0][0].callback_data == "setting_employer_direct"
    assert buttons[1][0].text == "Только ТОП-компании"
    assert buttons[1][0].callback_data == "setting_employer_top"

def test_get_save_cancel_keyboard():
    """Тест клавиатуры для сохранения/отмены настроек."""
    keyboard = get_save_cancel_keyboard()
    buttons = keyboard.inline_keyboard
    
    assert len(buttons) == 1  # Одна строка с двумя кнопками
    assert len(buttons[0]) == 2  # Две кнопки в строке
    assert buttons[0][0].text == "💾 Сохранить"
    assert buttons[0][0].callback_data == "settings_save"
    assert buttons[0][1].text == "❌ Отмена"
    assert buttons[0][1].callback_data == "settings_cancel"

def test_get_vacancy_actions_keyboard_with_apply_url():
    """Тест клавиатуры для действий с вакансией с URL для отклика."""
    vacancy_id = "12345"
    apply_url = "https://hh.ru/response"
    
    keyboard = get_vacancy_actions_keyboard(vacancy_id, apply_url)
    buttons = keyboard.inline_keyboard
    
    # Должно быть 3 кнопки: "Сгенерировать резюме", "Сохранить", "Откликнуться"
    assert len(buttons) == 3
    
    # Проверка кнопки "Сгенерировать резюме"
    assert buttons[0][0].text == "📄 Сгенерировать резюме"
    assert buttons[0][0].callback_data == f"vacancy_action|{vacancy_id}|generate_resume"
    
    # Проверка кнопки "Сохранить"
    assert buttons[1][0].text == "💾 Сохранить"
    assert buttons[1][0].callback_data == f"vacancy_action|{vacancy_id}|save"
    
    # Проверка кнопки "Откликнуться"
    assert buttons[2][0].text == "🔗 Откликнуться"
    assert buttons[2][0].url == apply_url
    assert buttons[2][0].callback_data is None  # URL кнопки не имеет callback_data

def test_get_vacancy_actions_keyboard_without_apply_url():
    """Тест клавиатуры для действий с вакансией без URL для отклика."""
    vacancy_id = "12345"
    
    keyboard = get_vacancy_actions_keyboard(vacancy_id)
    buttons = keyboard.inline_keyboard
    
    # Должно быть 2 кнопки: "Сгенерировать резюме", "Сохранить"
    assert len(buttons) == 2
    
    # Проверка кнопки "Сгенерировать резюме"
    assert buttons[0][0].text == "📄 Сгенерировать резюме"
    assert buttons[0][0].callback_data == f"vacancy_action|{vacancy_id}|generate_resume"
    
    # Проверка кнопки "Сохранить"
    assert buttons[1][0].text == "💾 Сохранить"
    assert buttons[1][0].callback_data == f"vacancy_action|{vacancy_id}|save"

def test_get_apply_confirmation_keyboard():
    """Тест клавиатуры для подтверждения отклика."""
    vacancy_id = "12345"
    
    keyboard = get_apply_confirmation_keyboard(vacancy_id)
    buttons = keyboard.inline_keyboard
    
    # Должна быть 1 кнопка
    assert len(buttons) == 1
    
    # Проверка кнопки подтверждения
    assert buttons[0][0].text == "✅ Я откликнулся на hh.ru"
    assert buttons[0][0].callback_data == f"confirm_applied|{vacancy_id}"