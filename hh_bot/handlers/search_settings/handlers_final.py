from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...db.models import User, SearchFilter
from ...utils.logger import logger
from .states import SearchSettingsStates


def register_final_handlers(router: Router):
    @router.callback_query(F.data == "settings_save", SearchSettingsStates.confirmation)
    async def save_settings(
        callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
    ):
        data = await state.get_data()
        user = await session.scalar(
            select(User).where(User.telegram_id == str(callback.from_user.id))
        )
        
        if user:
            search_filter = await session.scalar(select(SearchFilter).where(SearchFilter.user_id == user.id))
            if not search_filter:
                search_filter = SearchFilter(user_id=user.id)
            
            # ИСПРАВЛЕНИЕ: Используем .get() с значениями по умолчанию,
            # чтобы избежать присвоения None.
            search_filter.position = data.get("position")
            search_filter.city = data.get("city")
            search_filter.salary_min = data.get("salary_min")
            search_filter.remote = data.get("remote")
            search_filter.freshness_days = data.get("freshness_days")
            search_filter.employment = data.get("employment")
            
            session.add(search_filter)
            await session.commit()

        if callback:
            await callback.answer("Настройки успешно сохранены!")
        
        # ИСПРАВЛЕНИЕ: Безопасное редактирование сообщения
        try:
            if callback.message:
                await callback.message.edit_text("✅ Ваши настройки поиска сохранены.")
        except TelegramAPIError as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            
        await state.clear()

    @router.callback_query(F.data == "settings_cancel", SearchSettingsStates.confirmation)
    async def cancel_settings(callback: types.CallbackQuery, state: FSMContext):
        if callback:
            await callback.answer("Настройка отменена.")
        
        # ИСПРАВЛЕНИЕ: Безопасное редактирование сообщения
        try:
            if callback.message:
                await callback.message.edit_text("❌ Настройка отменена.")
        except TelegramAPIError as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            
        await state.clear()