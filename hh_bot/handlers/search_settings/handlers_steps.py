from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from ...keyboards.inline_keyboards import (
    get_remote_keyboard,
    get_freshness_keyboard,
    get_employment_keyboard,
    get_save_cancel_keyboard,
)
from ...utils.logger import logger
from .states import SearchSettingsStates


def register_steps_handlers(router: Router):
    @router.message(SearchSettingsStates.position)
    async def process_position(message: types.Message, state: FSMContext):
        await state.update_data(position=message.text)
        await message.answer("Отлично. Теперь укажите город для поиска:")
        await state.set_state(SearchSettingsStates.city)

    @router.message(SearchSettingsStates.city)
    async def process_city(message: types.Message, state: FSMContext):
        await state.update_data(city=message.text)
        await message.answer("Хорошо. Укажите минимальную зарплату (цифрами):")
        await state.set_state(SearchSettingsStates.salary_min)

    @router.message(SearchSettingsStates.salary_min)
    async def process_salary(message: types.Message, state: FSMContext):
        if not message.text or not message.text.isdigit():
            return await message.answer("Пожалуйста, введите зарплату цифрами.")

        await state.update_data(salary_min=int(message.text))
        await message.answer(
            "Готово. Искать удаленную работу?", reply_markup=get_remote_keyboard()
        )
        await state.set_state(SearchSettingsStates.remote)

    @router.callback_query(SearchSettingsStates.remote, F.data.startswith("setting_remote_"))
    async def process_remote(callback: types.CallbackQuery, state: FSMContext):
        if not callback.data:
            return
        is_remote = callback.data.split("_")[-1] == "yes"
        await state.update_data(remote=is_remote)
        try:
            await callback.message.edit_text(
                'Принято. Какая "свежесть" вакансий вас интересует?',
                reply_markup=get_freshness_keyboard(),
            )
        except TelegramAPIError as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")

        await state.set_state(SearchSettingsStates.freshness_days)
        if callback:
            await callback.answer()

    @router.callback_query(SearchSettingsStates.freshness_days, F.data.startswith("setting_freshness_"))
    async def process_freshness(callback: types.CallbackQuery, state: FSMContext):
        if not callback.data:
            return
        days = int(callback.data.split("_")[-1])
        await state.update_data(freshness_days=days)
        try:
            await callback.message.edit_text(
                "Хорошо. А какой тип занятости вас интересует?",
                reply_markup=get_employment_keyboard(),
            )
        except TelegramAPIError as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")

        await state.set_state(SearchSettingsStates.employment)
        if callback:
            await callback.answer()

    @router.callback_query(SearchSettingsStates.employment, F.data.startswith("setting_employment_"))
    async def process_employment_callback(callback: types.CallbackQuery, state: FSMContext):
        if not callback.data:
            return
        employment_type = callback.data.split("_")[-1]
        await state.update_data(employment=employment_type)
        if callback:
            await callback.answer(f"Выбран тип занятости: {employment_type}")
        try:
            await callback.message.edit_text(
                "Отлично! Настройки готовы. Нажмите '💾 Сохранить' для подтверждения или '❌ Отмена'.",
                reply_markup=get_save_cancel_keyboard(),
            )
        except TelegramAPIError as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
        await state.set_state(SearchSettingsStates.confirmation)

    @router.message(SearchSettingsStates.employment)
    async def process_employment_text_fallback(message: types.Message, state: FSMContext):
        await state.update_data(employment=message.text)
        await message.answer(
            "Тип занятости сохранен как текст. Нажмите '💾 Сохранить' для подтверждения.",
            reply_markup=get_save_cancel_keyboard(),
        )
        await state.set_state(SearchSettingsStates.confirmation)