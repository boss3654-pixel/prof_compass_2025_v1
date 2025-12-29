# hh_bot/handlers/errors.py
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from ..utils.logger import logger

errors_router = Router()

@errors_router.message(F.text)
async def catch_all_text_handler(message: types.Message, state: FSMContext):
    """
    Ловит все текстовые сообщения, которые не были обработаны ранее.
    Также логирует текущее состояние FSM для отладки.
    """
    # Получаем текущее состояние пользователя
    current_state = await state.get_state()
    
    # Логируем его вместе с сообщением
    logger.warning(
        f"Получено необработанное сообщение: '{message.text}'. "
        f"Текущее состояние FSM: {current_state}"
    )
    
    await message.answer("Извините, я не понял эту команду. Пожалуйста, используйте меню.")

@errors_router.callback_query(F.data)
async def catch_all_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """
    Ловит все нажатия кнопок, которые не были обработаны ранее.
    Также логирует текущее состояние FSM для отладки.
    """
    # Получаем текущее состояние пользователя
    current_state = await state.get_state()

    # Логируем его вместе с нажатием кнопки
    logger.warning(
        f"Получено необработанное нажатие кнопки: '{callback.data}'. "
        f"Текущее состояние FSM: {current_state}"
    )
    
    await callback.answer("Эта кнопка больше не активна.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error(f"Не удалось убрать клавиатуру у сообщения: {e}")