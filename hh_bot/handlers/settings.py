# hh_bot/handlers/settings.py

# --- ИМПОРТЫ ---

# Импорты из aiogram
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Импорты из SQLAlchemy для работы с БД
from sqlalchemy import select

# Импорты наших моделей БД
from ..db.models import User, SearchFilter, LLMSettings

# Импорты наших утилит
from ..utils.logger import logger

# Импорты дочерних роутеров
from .search_settings import search_settings_router
from .llm_settings import llm_settings_router

# --- ОСНОВНОЙ КОД ---

# Создаем главный роутер для настроек
router = Router()

# Включаем в него дочерние роутеры, чтобы их хэндлеры тоже работали
router.include_router(search_settings_router)
router.include_router(llm_settings_router)


# --- Хэндлеры меню ---


@router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(callback: types.CallbackQuery):
    """Показывает подменю для выбора типа настроек."""
    await callback.answer()
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🔍 Настройки поиска", callback_data="start_search_settings"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🤖 Настройки LLM", callback_data="start_llm_settings"
                )
            ],
        ]
    )
    await callback.message.answer(
        "Выберите, что хотите настроить:", reply_markup=keyboard
    )


# --- Финальные хэндлеры: Сохранение и Отмена ---
# Эти хэндлеры общие для обоих типов настроек, поэтому они остаются здесь.


@router.callback_query(F.data == "settings_save")
async def save_settings(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Сохраняет настройки (поиска или LLM) в базу данных."""
    user_data = await state.get_data()
    current_state = await state.get_state()

    # Проверка на случай, если состояние FSM было утеряно
    if current_state is None:
        await callback.message.edit_text(
            "Сессия настройки устарела. Пожалуйста, начните заново."
        )
        await callback.answer()
        return

    # Загружаем связанные сущности (llm_settings и search_filters)
    # чтобы избежать "ленивой" загрузки и ошибок типа greenlet_spawn
    user = await session.scalar(
        select(User)
        .options(selectinload(User.llm_settings), selectinload(User.search_filters))
        .where(User.telegram_id == str(callback.from_user.id))
    )
    if not user:
        await callback.message.edit_text("Ошибка: пользователь не найден.")
        await state.clear()
        return

    try:
        # Определяем, какого типа настройки мы сохраняем
        if "SearchSettings" in current_state:
            # Используем существующий фильтр или создаем новый
            settings_obj = user.search_filters or SearchFilter(user_id=user.id)
            session.add(settings_obj)

            for key in [
                "position",
                "city",
                "salary_min",
                "remote",
                "freshness_days",
                "employment",
            ]:
                value = user_data.get(key)
                # ИСПРАВЛЕНИЕ: Приводим значение для employment к верхнему регистру
                if key == "employment" and isinstance(value, str):
                    value = value.upper()
                setattr(settings_obj, key, value)

            msg = "✅ Ваши настройки поиска успешно сохранены!"

        elif "LLMSettings" in current_state:
            # Используем существующие настройки или создаем новые
            settings_obj = user.llm_settings or LLMSettings(user_id=user.id)

            # Устанавливаем все атрибуты, потом добавляем в сессию
            settings_obj.base_url = user_data.get("base_url")
            settings_obj.api_key = user_data.get("api_key")
            settings_obj.model_name = user_data.get("model_name")
            settings_obj.temperature = user_data.get(
                "temperature", 0.7
            )  # Устанавливаем значение по умолчанию

            session.add(settings_obj)
            msg = "✅ Ваши настройки LLM успешно сохранены!"
        else:
            raise ValueError("Неизвестное состояние для сохранения.")

        await session.commit()
        await callback.message.edit_text(msg)

    except Exception as e:
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сразу откатываем транзакцию, чтобы "починить" сессию
        await session.rollback()

        # Теперь можно безопасно логировать ошибку и общаться с пользователем
        logger.error(f"Error saving settings for user {user.id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении. Попробуйте позже."
        )
    finally:
        # В любом случае очищаем состояние FSM и отвечаем на callback
        await state.clear()
        await callback.answer()


@router.callback_query(F.data == "settings_cancel")
async def cancel_settings(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет процесс настройки и очищает состояние."""
    await state.clear()
    await callback.message.edit_text("Настройки отменены.")
    await callback.answer()
