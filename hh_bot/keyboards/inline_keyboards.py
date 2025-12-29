# hh_bot/keyboards/inline_keyboards.py

from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Клавиатуры для настроек поиска ---

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает главное меню бота.
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔍 Найти вакансии", callback_data="menu_search")
    )
    builder.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings"))
    builder.add(
        InlineKeyboardButton(text="📄 Мои резюме", callback_data="menu_resumes")
    )
    builder.adjust(1)  # Каждая кнопка на новой строке
    return builder.as_markup()


def get_remote_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data="setting_remote_yes"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data="setting_remote_no"))
    builder.adjust(2)  # Кнопки в одну строку
    return builder.as_markup()


def get_freshness_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="За 1 день", callback_data="setting_freshness_1")
    )
    builder.add(
        InlineKeyboardButton(text="За 3 дня", callback_data="setting_freshness_3")
    )
    builder.add(
        InlineKeyboardButton(text="За 7 дней", callback_data="setting_freshness_7")
    )
    builder.adjust(1)  # Каждая кнопка на новой строке
    return builder.as_markup()


def get_employment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа занятости."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Полная занятость", callback_data="setting_employment_full"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Частичная занятость", callback_data="setting_employment_part"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Стажировка", callback_data="setting_employment_internship"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Проектная работа", callback_data="setting_employment_project"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора опыта работы."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Нет опыта", callback_data="setting_experience_noExperience"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="От 1 года до 3 лет", callback_data="setting_experience_between1And3"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="От 3 до 6 лет", callback_data="setting_experience_between3And6"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Более 6 лет", callback_data="setting_experience_moreThan6"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def get_employer_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа работодателя."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Только прямые работодатели", callback_data="setting_employer_direct"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Только ТОП-компании", callback_data="setting_employer_top"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def get_save_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="settings_save")
    )
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="settings_cancel"))
    builder.adjust(2)
    return builder.as_markup()


# --- Клавиатуры для настроек LLM ---
def get_llm_save_cancel_keyboard():
    # Используем ту же клавиатуру, но можно создать свою с другими текстами
    return get_save_cancel_keyboard()


def get_vacancy_actions_keyboard(vacancy_hh_id: str, apply_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру для действий с вакансией."""
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Сгенерировать резюме"
    builder.row(
        InlineKeyboardButton(text="📄 Сгенерировать резюме", callback_data=f"vacancy_action|{vacancy_hh_id}|generate_resume")
    )
    
    # Кнопка "Сохранить"
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data=f"vacancy_action|{vacancy_hh_id}|save")
    )
    
    # Кнопка "Откликнуться" (если есть ссылка)
    if apply_url:
        builder.row(
            InlineKeyboardButton(text="🔗 Откликнуться", url=apply_url)
        )
    
    return builder.as_markup()

def get_apply_confirmation_keyboard(vacancy_hh_id: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для подтверждения отклика.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я откликнулся на hh.ru", callback_data=f"confirm_applied|{vacancy_hh_id}")
    return builder.as_markup()