from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...db.models import User
from .states import SearchSettingsStates


def register_start_handlers(router: Router):
    @router.callback_query(F.data == "start_search_settings")
    async def start_search_settings(
        callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
    ):
        """Начинает процесс настройки поиска."""
        if callback:
            await callback.answer()

        stmt = (
            select(User)
            .options(selectinload(User.search_filters))
            .where(User.telegram_id == str(callback.from_user.id))
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            if callback.message:
                await callback.message.answer(
                    "Сначала вам нужно зарегистрироваться с помощью команды /start"
                )
            return

        if user.search_filters:
            await state.set_data(
                {
                    "position": user.search_filters.position,
                    "city": user.search_filters.city,
                    "salary_min": user.search_filters.salary_min,
                    "remote": user.search_filters.remote,
                    "freshness_days": user.search_filters.freshness_days,
                    "employment": user.search_filters.employment,
                }
            )
            if callback.message:
                await callback.message.answer(
                    "Вы уже настраивали поиск ранее. Вы можете изменить параметры. Введите желаемую должность:"
                )
        else:
            if callback.message:
                await callback.message.answer(
                    "Давайте настроим параметры поиска. Введите желаемую должность:"
                )

        await state.set_state(SearchSettingsStates.position)