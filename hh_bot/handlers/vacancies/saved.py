# hh_bot/handlers/vacancies/saved.py
from aiogram import F, types, Router
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

# ИСПРАВЛЕННЫЕ ИМПОРТЫ
from ...db.models import User, Vacancy, UserVacancyStatus
from ...keyboards.inline_keyboards import get_vacancy_actions_keyboard, get_main_menu_keyboard
from ...utils.logger import logger

# Роутер для сохраненных вакансий
saved_router = Router()

# --- Вспомогательная функция ---
async def _get_vacancy_texts_for_user(session: AsyncSession, user_id: str) -> list[tuple[str, types.InlineKeyboardMarkup]]:
    # ... (код функции без изменений) ...
    stmt = (
        select(User)
        .options(selectinload(User.viewed_vacancies).selectinload(UserVacancyStatus.vacancy))
        .where(User.telegram_id == user_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.viewed_vacancies:
        return []

    vacancy_data = []
    for user_vacancy in user.viewed_vacancies:
        if user_vacancy.status in ["sent", "viewed"]:
            vac = user_vacancy.vacancy
            salary_text = f"от {vac.salary}" if vac.salary else "Не указана"
            text = (
                f"🏢 *{vac.title}*\n"
                f"📍 Компания: {vac.company}\n"
                f"💰 Зарплата: {salary_text}\n"
                f"🔗 [Смотреть вакансию]({vac.link})"
            )
            keyboard = get_vacancy_actions_keyboard(vac.hh_id)
            vacancy_data.append((text, keyboard))
            if user_vacancy.status == "sent":
                user_vacancy.status = "viewed"
    return vacancy_data

# --- Хэндлеры меню ---
@saved_router.callback_query(F.data == "menu_search")
async def handle_vacancies_menu(callback: types.CallbackQuery):
    """Показывает подменю для поиска вакансий."""
    await callback.answer()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔎 Начать новый поиск", callback_data="start_new_search")],
        [types.InlineKeyboardButton(text="📋 Мои сохраненные вакансии", callback_data="view_saved_vacancies")],
        [types.InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="menu_main")],
    ])
    await callback.message.answer("Выберите действие:", reply_markup=keyboard)

@saved_router.callback_query(F.data == "menu_main")
async def handle_main_menu(callback: types.CallbackQuery):
    """Возвращает пользователя в главное меню."""
    await callback.answer()
    await callback.message.answer("Вы в главном меню:", reply_markup=get_main_menu_keyboard())

# --- Хэндлеры для просмотра сохраненных вакансий ---
@saved_router.message(Command("vacancies"))
async def cmd_show_vacancies(message: types.Message, session: AsyncSession):
    """Показывает вакансии по команде."""
    vacancy_data = await _get_vacancy_texts_for_user(session, str(message.from_user.id))
    if not vacancy_data:
        await message.answer("Для вас пока нет вакансий.")
        return
    for text, keyboard in vacancy_data:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@saved_router.callback_query(F.data == "view_saved_vacancies")
async def handle_view_saved_vacancies(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает сохраненные вакансии по кнопке."""
    await callback.answer()
    vacancy_data = await _get_vacancy_texts_for_user(session, str(callback.from_user.id))
    if not vacancy_data:
        await callback.message.answer("У вас пока нет сохраненных вакансий.")
        return
    for text, keyboard in vacancy_data:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")