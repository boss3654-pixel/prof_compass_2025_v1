# hh_bot/handlers/llm_settings.py

from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import User, LLMSettings
from ..keyboards.inline_keyboards import get_save_cancel_keyboard
from ..utils.logger import logger

# Создаем отдельный роутер для настроек LLM
llm_settings_router = Router()


# --- FSM-группы состояний ---
class LLMSettingsStates(StatesGroup):
    base_url = State()
    api_key = State()
    model_name = State()


# --- Хэндлеры настроек LLM ---


@llm_settings_router.callback_query(F.data == "start_llm_settings")
async def start_llm_settings(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🚀 Использовать OpenRouter",
                    callback_data="configure_openrouter",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="⚙️ Настроить вручную", callback_data="configure_llm_manually"
                )
            ],
        ]
    )
    await callback.message.answer(
        "Выберите способ настройки LLM:", reply_markup=keyboard
    )


@llm_settings_router.callback_query(F.data == "configure_openrouter")
async def configure_openrouter(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    # Предзаполняем данные для OpenRouter
    await state.set_data(
        {
            "base_url": "https://openrouter.ai/api/v1",
            "model_name": "meta-llama/llama-3.1-8b-instruct:free",
        }
    )
    await callback.message.edit_text(
        "Отлично! Я выберу стандартные настройки для OpenRouter.\n\n"
        "🔑 Теперь просто введите ваш API-ключ от OpenRouter:"
    )
    await state.set_state(LLMSettingsStates.api_key)


@llm_settings_router.callback_query(F.data == "configure_llm_manually")
async def configure_llm_manually(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Хорошо. Введите Base URL вашего API:")
    await state.set_state(LLMSettingsStates.base_url)


@llm_settings_router.message(LLMSettingsStates.base_url)
async def process_llm_base_url(message: types.Message, state: FSMContext):
    await state.update_data(base_url=message.text)
    await message.answer("Хорошо. Теперь введите ваш API Key:")
    await state.set_state(LLMSettingsStates.api_key)


@llm_settings_router.message(LLMSettingsStates.api_key)
async def process_llm_api_key(message: types.Message, state: FSMContext):
    await state.update_data(api_key=message.text)
    await message.answer(
        "Отлично. И последнее, введите название модели (например, gpt-3.5-turbo):"
    )
    await state.set_state(LLMSettingsStates.model_name)


@llm_settings_router.message(LLMSettingsStates.model_name)
async def process_llm_model_name(message: types.Message, state: FSMContext):
    await state.update_data(model_name=message.text)
    await message.answer(
        "Настройки сохранены! Нажмите '💾 Сохранить' для подтверждения.",
        reply_markup=get_save_cancel_keyboard(),
    )
