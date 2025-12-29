import asyncio
from aiogram import F, types, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import User, Vacancy, UserVacancyStatus
from ...services.llm_service import generate_resume, generate_cover_letter
from ...utils.logger import logger

actions_router = Router()


# Внутренняя функция для устранения дублирования
async def _generate_and_send(
    callback: types.CallbackQuery,
    generation_func: callable,
    success_message_prefix: str,
    vacancy_info: dict,
    user_profile: dict,
    llm_settings: dict,
):
    """Внутренняя функция для генерации и отправки текста с тайм-аутом и индикацией."""
    try:
        # Показываем пользователю, что бот что-то делает
        await callback.bot.send_chat_action(
            chat_id=callback.message.chat.id, action="typing"
        )

        # Устанавливаем тайм-аут в 90 секунд для генерации
        # Это не даст боту "зависнуть", если LLM API будет отвечать слишком долго
        text = await asyncio.wait_for(
            generation_func(vacancy_info, user_profile, llm_settings), timeout=90.0
        )

        await callback.message.answer(
            f"{success_message_prefix}:\n\n{text}", parse_mode="HTML"
        )

    except asyncio.TimeoutError:
        # Обрабатываем случай, когда генерация заняла слишком много времени
        logger.warning(f"LLM generation timed out for user {callback.from_user.id}")
        await callback.message.answer(
            "⏳ Генерация заняла слишком много времени. Пожалуйста, попробуйте позже."
        )
    except Exception as e:
        # Обрабатываем другие возможные ошибки (например, ошибка API LLM)
        logger.error(f"Error in {generation_func.__name__}: {e}")
        await callback.message.answer(
            f"❌ Произошла ошибка при генерации. Попробуйте позже."
        )


@actions_router.callback_query(F.data.startswith("vacancy_action|"))
async def process_vacancy_action(callback: types.CallbackQuery, session: AsyncSession):
    """Обрабатывает нажатия на кнопки под вакансией."""
    try:
        _, hh_id, action = callback.data.split("|")
    except ValueError:
        logger.error(f"Неверный формат callback_data: {callback.data}")
        await callback.answer("Ошибка в данных кнопки.", show_alert=True)
        return

    if not hh_id or not hh_id.isdigit():
        logger.error(
            f"Получен некорректный hh_id '{hh_id}' из callback_data: {callback.data}"
        )
        await callback.answer(
            "Ошибка в данных кнопки: неверный ID вакансии.", show_alert=True
        )
        return

    # Выполняем запросы к БД параллельно для ускорения
    user_result, vacancy_result = await asyncio.gather(
        session.scalar(
            select(User)
            .options(selectinload(User.llm_settings))
            .where(User.telegram_id == str(callback.from_user.id))
        ),
        session.scalar(select(Vacancy).where(Vacancy.hh_id == hh_id)),
    )
    user = user_result
    vacancy = vacancy_result

    if not user or not vacancy:
        logger.warning(
            f"Не найден пользователь или вакансия для callback_data: {callback.data}"
        )
        await callback.message.edit_text("Не удалось найти пользователя или вакансию.")
        await callback.answer()
        return

    if action in ["generate_resume", "generate_cover_letter"]:
        if not user.llm_settings:
            await callback.message.answer(
                "⚠️ Сначала настройте ваш LLM API в меню настроек."
            )
            await callback.answer()
            return

        llm_settings = {
            "base_url": user.llm_settings.base_url,
            "api_key": user.llm_settings.api_key,
            "model_name": user.llm_settings.model_name,
        }
        vacancy_info = {
            "title": vacancy.title,
            "company": vacancy.company,
            "snippet": vacancy.description_snippet,
        }
        user_profile = {
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "base_resume": user.base_resume,
        }

        if action == "generate_resume":
            await callback.message.answer("🔄 Генерирую резюме...")
            await _generate_and_send(
                callback,
                generate_resume,
                "📄 *Адаптированное резюме*",
                vacancy_info,
                user_profile,
                llm_settings,
            )
        elif action == "generate_cover_letter":
            await callback.message.answer("🔄 Генерирую письмо...")
            await _generate_and_send(
                callback,
                generate_cover_letter,
                "✉️ *Сопроводительное письмо*",
                vacancy_info,
                user_profile,
                llm_settings,
            )

    elif action == "not_interested":
        status_to_update = await session.scalar(
            select(UserVacancyStatus).where(
                UserVacancyStatus.user_id == user.id,
                UserVacancyStatus.vacancy_id == vacancy.id,
            )
        )

        if status_to_update:
            status_to_update.status = "not_interested"
        else:
            new_status = UserVacancyStatus(
                user_id=user.id, vacancy_id=vacancy.id, status="not_interested"
            )
            session.add(new_status)

        await session.commit()

        await callback.answer("Отмечено как 'Неинтересно'")
        try:
            if callback.message.reply_markup:
                keyboard = callback.message.reply_markup.inline_keyboard
                for row in keyboard:
                    for button in row:
                        if button.callback_data == callback.data:
                            button.text = "✅ Неинтересно"
                            # Делаем кнопку неактивной
                            button.callback_data = None
                            break
                await callback.message.edit_reply_markup(
                    reply_markup=callback.message.reply_markup
                )
        except Exception as e:
            # Если сообщение старое, его нельзя отредактировать. Просто логируем.
            logger.warning(f"Could not edit message markup: {e}")

    else:
        await callback.answer("Неизвестное действие.", show_alert=True)
