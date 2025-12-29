# hh_bot/handlers/confirmations.py

from aiogram import F, types, Router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.models import User, Vacancy, UserVacancyStatus
from ..enums import UserVacancyStatusEnum
from ..utils.logger import logger
from ..keyboards.inline_keyboards import get_vacancy_actions_keyboard

# Создаем роутер для подтверждений
confirmation_router = Router(name="confirmations")

@confirmation_router.callback_query(F.data.startswith("confirm_applied|"))
async def handle_confirm_applied(callback: types.CallbackQuery, session: AsyncSession, user: User):
    if not callback.data:
        return

    await callback.answer("Спасибо за подтверждение!", show_alert=True) # type: ignore

    _, vacancy_hh_id_str = callback.data.split('|')
    vacancy_obj = await session.scalar(select(Vacancy).where(Vacancy.hh_id == vacancy_hh_id_str))
    
    if not vacancy_obj:
        if not callback.message: return
        await callback.message.answer("❌ Не удалось найти эту вакансию в нашей базе.")
        return

    status_obj = await session.scalar(
        select(UserVacancyStatus).where(
            (UserVacancyStatus.user_id == user.id) & (UserVacancyStatus.vacancy_id == vacancy_obj.id)
        )
    )

    if status_obj:
        status_obj.status = UserVacancyStatusEnum.VIEWED # type: ignore
    else:
        new_status = UserVacancyStatus(
            user_id=user.id, vacancy_id=vacancy_obj.id,
            status=UserVacancyStatusEnum.VIEWED # type: ignore
        )
        session.add(new_status)

    await session.commit()
    
    confirmation_text = (
        f"✅ Отлично! Ваш отклик на вакансию '{vacancy_obj.title}' подтвержден.\n\n"
        "Что бы вы хотели сделать дальше?"
    )
    
    if not callback.message: return
    await callback.message.answer(
        confirmation_text,
        reply_markup=get_vacancy_actions_keyboard(vacancy_hh_id_str)
    )