# hh_bot/middlewares.py

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db.models import User as DBUser  # Переименовываем, чтобы избежать конфликта имен
from .utils.logger import logger


class DbSessionMiddleware(BaseMiddleware):
    """
    Этот middleware предоставляет сессию базы данных и объект пользователя
    в данные хэндлера.
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session

            # ИСПРАВЛЕНО: Получаем пользователя из data, куда его положил aiogram
            telegram_user: Optional[User] = data.get("event_from_user")

            if telegram_user:
                # Преобразуем ID пользователя в строку
                telegram_id_str = str(telegram_user.id)

                # Ищем пользователя в базе данных по строковому ID
                db_user = await session.scalar(
                    select(DBUser).where(DBUser.telegram_id == telegram_id_str)
                )

                # Если пользователя нет, создаем его
                if not db_user:
                    db_user = DBUser(
                        telegram_id=telegram_id_str,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name,
                        last_name=telegram_user.last_name,
                    )
                    session.add(db_user)
                    await session.commit()
                    await session.refresh(
                        db_user
                    )  # Обновляем объект, чтобы получить ID из БД
                    logger.info(
                        f"Создан новый пользователь с telegram_id {telegram_id_str}"
                    )

                # Добавляем объект пользователя из БД в данные под ключом 'user'
                data["user"] = db_user
                logger.info(
                    f"Пользователь {db_user.full_name or db_user.telegram_id} добавлен в data['user']"
                )

            # Вызываем хэндлер, передавая ему обновленные данные
            return await handler(event, data)
