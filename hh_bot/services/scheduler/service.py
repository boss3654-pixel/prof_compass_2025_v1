"""
Модуль для управления жизненным циклом планировщика APScheduler.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram import Bot

from hh_bot.utils.logger import logger
from .jobs import daily_digest_job

# Создаем экземпляр планировщика на уровне модуля
scheduler = AsyncIOScheduler()


def setup_scheduler(
    bot: Bot,
    async_session_maker: async_sessionmaker[AsyncSession]
):
    """
    Инициализация и запуск планировщика задач.

    Args:
        bot: Экземпляр бота aiogram, который будет передан в задачи.
        async_session_maker: Фабрика сессий для работы с БД.
    """
    scheduler.add_job(
        daily_digest_job,
        trigger=CronTrigger(hour=9, minute=0), # Запуск каждый день в 9:00 по МСК
        # Передаем зависимости в функцию daily_digest_job через kwargs
        kwargs={"bot": bot, "async_session_maker": async_session_maker}, # type: ignore
        id="daily_digest_job",
        name="Ежедневная рассылка вакансий",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Планировщик задач запущен. Ежедневная рассылка назначена на 9:00 по МСК.")


def shutdown_scheduler():
    """
    Корректная остановка планировщика задач.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик задач остановлен.")