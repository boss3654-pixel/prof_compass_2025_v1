# hh_bot/handlers/menu_handlers.py

from aiogram import F, types, Router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db.models import User, GeneratedDocument
from ..enums import DocumentTypeEnum
from ..services.search_service import process_search_results
from ..utils.logger import logger

# Создаем роутер для меню
menu_handlers_router = Router(name="menu_handlers")

@menu_handlers_router.callback_query(F.data == "menu_resumes")
async def handle_resumes_menu(callback: types.CallbackQuery, session: AsyncSession, user: User):
    """Обработчик кнопки 'Мои резюме'."""
    await callback.answer() # type: ignore
    
    # ИСПРАВЛЕНИЕ: Добавлена проверка на None для большей надежности
    if not callback.message:
        return

    try:
        # Ищем все документы типа RESUME для текущего пользователя
        result = await session.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.user_id == user.id)
            .where(GeneratedDocument.doc_type == DocumentTypeEnum.RESUME)
            .order_by(GeneratedDocument.created_at.desc())
        )
        resumes = result.scalars().all()

        if not resumes:
            await callback.message.answer("У вас пока нет сгенерированных резюме.")
            return

        response_text = "📄 *Ваши сгенерированные резюме:*\n\n"
        for i, resume in enumerate(resumes, 1):
            response_text += f"{i}. Резюме от {resume.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

        await callback.message.answer(response_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при попытке получить резюме для пользователя {user.id}: {e}")
        await callback.message.answer("Не удалось загрузить список резюме. Попробуйте позже.")


@menu_handlers_router.callback_query(F.data == "menu_search")
async def handle_search_menu(callback: types.CallbackQuery, session: AsyncSession, user: User):
    """Обработчик кнопки 'Поиск вакансий'."""
    await callback.answer() # type: ignore

    # ИСПРАВЛЕНИЕ: Добавлена проверка на None для большей надежности
    if not callback.message:
        return
    
    # Загружаем пользователя с его настройками поиска
    stmt = select(User).options(selectinload(User.search_filters)).where(User.telegram_id == str(callback.from_user.id))
    result = await session.execute(stmt)
    user_with_filters = result.scalar_one_or_none()

    if not user_with_filters or not user_with_filters.search_filters:
        await callback.message.answer(
            "⚠️ У вас не настроены фильтры для поиска.\n"
            "Пожалуйста, сначала настройте параметры в меню 'Настройки поиска'."
        )
        return

    # Создаем словарь с фильтрами для функции поиска
    filters = user_with_filters.search_filters
    filters_dict = {
        "position": filters.position,
        # !!! ВАЖНО: hh.ru ожидает ID города (area), а не его название.
        # Нужно будет реализовать функцию для поиска ID города по названию.
        # Пока поиск по городу может работать некорректно.
        "city": filters.city, 
        "salary_min": filters.salary_min,
        "remote": filters.remote,
        "freshness_days": filters.freshness_days,
        # --- ИСПРАВЛЕНО: Получаем строковое значение из Enum ---
        "employment": filters.employment.value if filters.employment else None,
        "experience": filters.experience.value if filters.experience else None,
    }

    # Вызываем основную функцию поиска
    await process_search_results(
        message=callback.message,
        state=None, # Здесь не используется FSM, но функция требует этот аргумент
        session=session,
        user=user_with_filters,
        filters_dict=filters_dict
    )