from aiogram import F, types, Router, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# ДОБАВЛЕНО: импортируем UserVacancyStatus
from ..db.models import User, GeneratedDocument, Vacancy, UserVacancyStatus
from ..enums import DocumentTypeEnum, UserVacancyStatusEnum
from ..utils.logger import logger
from ..utils.resume_generator import generate_resume_for_vacancy
from ..utils.cover_letter_generator import generate_cover_letter_for_vacancy
from ..keyboards.inline_keyboards import get_apply_confirmation_keyboard

# Создаем роутер для генерации документов
document_generation_router = Router(name="document_generation")

@document_generation_router.callback_query(F.data.startswith("vacancy_action|"))
async def handle_document_generation(callback: types.CallbackQuery, session: AsyncSession, user: User):
    # 1. ИЗМЕНЕНИЕ: Сразу отвечаем на callback, чтобы убрать "часики".
    # show_alert=False, чтобы не показывать всплывающее окно, т.к. мы будем отправлять сообщение.
    await callback.answer(show_alert=False)

    if not callback.data or not callback.message:
        logger.warning("Callback query без данных или сообщения.")
        return

    try:
        _, vacancy_id_str, action = callback.data.split('|')
        vacancy_hh_id = int(vacancy_id_str)
        user_id = int(user.id) # type: ignore

        # Находим объект вакансии ОДИН РАЗ в самом начале
        vacancy_obj = await session.scalar(select(Vacancy).where(Vacancy.hh_id == str(vacancy_hh_id)))
        if not vacancy_obj:
            await callback.message.answer("❌ Не удалось найти вакансию. Возможно, она была удалена.")
            raise ValueError(f"Вакансия с hh_id={vacancy_hh_id} не найдена")

        # --- ЛОГИКА ГЕНЕРАЦИИ РЕЗЮМЕ ---
        if action == "generate_resume":
            processing_message = await callback.message.answer("⏳ Генерирую резюме, это может занять некоторое время...")
            
            try:
                resume_text = await generate_resume_for_vacancy(
                    vacancy_id=vacancy_hh_id, user_id=user_id, session=session
                )

                new_resume_doc = GeneratedDocument(
                    user_id=user_id, vacancy_id=vacancy_obj.id,
                    doc_type=DocumentTypeEnum.RESUME, content=resume_text
                )
                session.add(new_resume_doc)
                await session.commit()

                await processing_message.edit_text(
                    f"📄 Вот ваше резюме:\n\n```\n{resume_text}\n```", parse_mode="MarkdownV2"
                )
            except ValueError as e:
                logger.warning(f"Не удалось сгенерировать резюме для вакансии {vacancy_hh_id}: {e}")
                await processing_message.edit_text(f"❌ Произошла ошибка: {str(e)}")

        # --- ЛОГИКА ГЕНЕРАЦИИ СОПРОВОДИТЕЛЬНОГО ПИСЬМА ---
        elif action == "generate_cover":
            processing_message = await callback.message.answer("⏳ Генерирую сопроводительное письмо...")

            try:
                cover_letter_text = await generate_cover_letter_for_vacancy(
                    vacancy_id=vacancy_hh_id, user_id=user_id, session=session
                )

                new_cover_doc = GeneratedDocument(
                    user_id=user_id, vacancy_id=vacancy_obj.id,
                    doc_type=DocumentTypeEnum.COVER_LETTER, content=cover_letter_text
                )
                session.add(new_cover_doc)
                await session.commit()

                apply_url = vacancy_obj.apply_url or vacancy_obj.link
                response_text = (
                    f"📄 Вот ваше сопроводительное письмо:\n\n```\n{cover_letter_text}\n```\n\n"
                    f"🔗 [Перейти к отклику на hh.ru]({apply_url})\n\n"
                    f"После отправки отклика нажмите кнопку ниже, чтобы подтвердить:"
                )
                await processing_message.edit_text(
                    response_text, parse_mode="MarkdownV2",
                    reply_markup=get_apply_confirmation_keyboard(str(vacancy_hh_id))
                )
            except ValueError as e:
                logger.warning(f"Не удалось сгенерировать письмо для вакансии {vacancy_hh_id}: {e}")
                await processing_message.edit_text(f"❌ Произошла ошибка: {str(e)}")
        
        # --- ЛОГИКА: СОХРАНЕНИЕ ВАКАНСИИ ---
        elif action == "save":
            # 2. ИЗМЕНЕНИЕ: Более стандартное логирование
            logger.info(f"Пользователь {user_id} сохраняет вакансию {vacancy_hh_id}")

            # Проверяем, не сохранили ли мы эту вакансию уже
            existing_status = await session.scalar(
                select(UserVacancyStatus).where(
                    (UserVacancyStatus.user_id == user_id) &
                    (UserVacancyStatus.vacancy_id == vacancy_obj.id)
                )
            )
            
            if existing_status:
                await callback.message.answer("⚠️ Эта вакансия уже у вас в сохраненных.")
                return

            # Создаем новую запись о статусе вакансии
            # Примечание: используется статус SENT, т.к. он означает "взаимодействие начато".
            # В будущем можно добавить отдельный статус SAVED в UserVacancyStatusEnum.
            new_status = UserVacancyStatus(
                user_id=user_id,
                vacancy_id=vacancy_obj.id,
                status=UserVacancyStatusEnum.SENT
            )
            session.add(new_status)
            await session.commit()

            # 3. ИЗМЕНЕНИЕ: Более точное сообщение для пользователя
            await callback.message.answer("✅ Вакансия сохранена! Вы сможете найти её в истории ваших взаимодействий.")


    except ValueError as e:
        # Эта ошибка уже обработана внутри блоков, но на всякий случай оставим лог
        logger.error(f"Ошибка в handle_document_generation (ValueError): {e}")
    except Exception as e:
        # 4. ИЗМЕНЕНИЕ: Убедимся, что callback.message существует перед отправкой
        logger.error(f"Непредвиденная ошибка в handle_document_generation: {e}", exc_info=True)
        if callback.message:
            await callback.message.answer("❌ К сожалению, произошла непредвиденная ошибка. Попробуйте позже.")
