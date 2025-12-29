# hh_bot/handlers/registration.py

from aiogram import F, types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import User
from ..keyboards.inline_keyboards import get_main_menu_keyboard
from ..utils.logger import logger

# Создаем роутер для регистрации
registration_router = Router(name="registration")

# --- Состояния для регистрации ---
class RegistrationStates(StatesGroup):
    full_name = State()
    city = State()
    desired_position = State()
    skills = State()
    base_resume = State()


# --- Хэндлеры регистрации ---
@registration_router.message(Command("start"))
async def cmd_start(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    if (
        user.full_name and user.city and user.desired_position
        and user.skills and user.base_resume
    ):
        await message.answer(
            f"С возвращением, {user.full_name}! Вот главное меню:",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await message.answer(
        "Добро пожаловать! Давайте начнем регистрацию.\n\n"
        "Как вас зовут (имя и фамилия)?"
    )
    await state.set_state(RegistrationStates.full_name)
    logger.info(
        f"Пользователь {user.id} (tg: {user.telegram_id}) начал/продолжил регистрацию."
    )

@registration_router.message(RegistrationStates.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите ваше имя текстом.")
    await state.update_data(full_name=message.text)
    await message.answer("Отлично! В каком вы городе?")
    await state.set_state(RegistrationStates.city)

@registration_router.message(RegistrationStates.city)
async def process_city(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите название города текстом.")
    await state.update_data(city=message.text)
    await message.answer("Хорошо. Какую должность вы ищете?")
    await state.set_state(RegistrationStates.desired_position)

@registration_router.message(RegistrationStates.desired_position)
async def process_desired_position(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите желаемую должность текстом.")
    await state.update_data(desired_position=message.text)
    await message.answer(
        "Теперь перечислите ваши ключевые навыки через запятую.\n"
        "Например: Python, SQL, Git, Docker"
    )
    await state.set_state(RegistrationStates.skills)

@registration_router.message(RegistrationStates.skills)
async def process_skills(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, перечислите навыки текстом.")
    await state.update_data(skills=message.text)
    await message.answer(
        "Отлично! И последний шаг.\n\n"
        "Напишите краткое описание вашего опыта или прикрепите существующее резюме."
    )
    await state.set_state(RegistrationStates.base_resume)

@registration_router.message(RegistrationStates.base_resume)
async def process_base_resume(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    user_data = await state.get_data()
    user.full_name = user_data.get("full_name")
    user.city = user_data.get("city")
    user.desired_position = user_data.get("desired_position")
    user.skills = user_data.get("skills")
    user.base_resume = message.text if message.text else message.caption
    await session.commit()

    await message.answer(
        "Отлично, регистрация завершена! Добро пожаловать в главное меню.",
        reply_markup=get_main_menu_keyboard(),
    )
    await state.clear()
    logger.info(
        f"Пользователь {user.id} (tg: {user.telegram_id}) завершил регистрацию."
    )