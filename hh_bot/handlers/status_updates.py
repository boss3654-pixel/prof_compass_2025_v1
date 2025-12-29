# hh_bot/handlers/status_updates.py

from aiogram import F, types, Router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.models import User, Vacancy, UserVacancyStatus
from ..enums import UserVacancyStatusEnum
from ..utils.logger import logger
from ..keyboards.inline_keyboards import get_vacancy_actions_keyboard

# Создаем роутер для обновления статусов
status_updates_router = Router(name="status_updates")

@status_updates_router.callback_query(F.data.startswith("vacancy_action|"))
async def handle_status_update(callback: types.CallbackQuery, session: AsyncSession, user: User):
    if not callback.data:
        return
        
    await callback.answer() # type: ignore

    try:
        _, vacancy_id_str, action = callback.data.split('|')
        vacancy_hh_id = int(vacancy_id_str)
        user_id = int(user.id) # type: ignore

        # --- ЛОГИКА ПОДТВЕРЖДЕНИЯ "НЕ ИНТЕРЕСНО" ---
        if action == "not_interested":
            vacancy_obj = await session.scalar(select(Vacancy).where(Vacancy.hh_id == str(vacancy_hh_id)))
            if not vacancy_obj:
                if not callback.message: return
                await callback.message.answer("❌ Не удалось найти эту вакансию в нашей базе.")
                return

            status_obj = await session.scalar(
                select(UserVacancyStatus).where(
                    (UserVacancyStatus.user_id == user_id) & (UserVacancyStatus.vacancy_id == vacancy_obj.id)
                )
            )

            if status_obj:
                status_obj.status = UserVacancyStatusEnum.NOT_INTERESTED # type: ignore
            else:
                new_status = UserVacancyStatus(
                    user_id=user_id, vacancy_id=vacancy_obj.id,
                    status=UserVacancyStatusEnum.NOT_INTERESTED # type: ignore
                )
                session.add(new_status)
            
            await session.commit()
            if not callback.message: return
            await callback.message.answer("👍 Хорошо, я учту, что эта вакансия вам не интересна.")

        # --- ЛОГИКА СОХРАНЕНИЯ ---
        elif action == "save":
            if not callback.message: return
            await callback.message.answer(f"✅ Вакансия {vacancy_hh_id} сохранена в избранное.")

    except Exception as e:
        logger.error(f"Непредвиденная ошибка в handle_status_update: {e}")
        if callback.message:
            await callback.message.answer("❌ К сожалению, произошла непредвиденная ошибка. Попробуйте позже.")
