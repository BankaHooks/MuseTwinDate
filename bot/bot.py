import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select, func
from datetime import datetime, timedelta
from config import config
from database.db import engine, Base, AsyncSessionLocal
from database import crud
from database.models import User
from handlers import start, menu, browse, likes, profile, premium, report, admin, ai
import random

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)

class ActivityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        result = await handler(event, data)
        user = data.get("user")
        session = data.get("session")
        if user and session:
            try:
                user.last_activity = datetime.utcnow()
                await session.commit()
            except Exception as e:
                logger.error(f"Error updating activity: {e}")
        return result

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

async def inactivity_notifier():
    while True:
        await asyncio.sleep(86400)
        try:
            async with AsyncSessionLocal() as session:
                cutoff = datetime.utcnow() - timedelta(days=7)
                stmt = select(User).where(
                    User.last_activity < cutoff,
                    (User.last_inactivity_notification < cutoff) | (User.last_inactivity_notification == None)
                )
                result = await session.execute(stmt)
                users = result.scalars().all()
                for user in users:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "Несколько людей с похожим музыкальным вкусом хотят познакомиться с тобой. Зайди и посмотри!"
                        )
                        user.last_inactivity_notification = datetime.utcnow()
                        await session.commit()
                    except Exception as e:
                        logger.error(f"Failed to send inactivity notification to {user.telegram_id}: {e}")
        except Exception as e:
            logger.error(f"Error in inactivity_notifier: {e}")

async def fake_activity_simulator():
    while True:
        await asyncio.sleep(random.randint(1800, 7200))
        try:
            async with AsyncSessionLocal() as session:
                bot_user = await crud.get_random_bot(session)
                if not bot_user:
                    continue
                user = await crud.get_random_real_user(session)
                if not user:
                    continue
                existing = await crud.get_like_between(session, bot_user.id, user.id)
                if existing:
                    continue
                like = await crud.create_like(session, bot_user.id, user.id)
                if like:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            f"🎵 У вас новый лайк от пользователя {bot_user.name or bot_user.username}!"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send fake like notification: {e}")
        except Exception as e:
            logger.error(f"Error in fake_activity_simulator: {e}")

async def main():
    global bot
    storage = MemoryStorage()
    if config.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            from redis.asyncio import Redis
            redis = Redis.from_url(config.REDIS_URL)
            storage = RedisStorage(redis)
            logger.info("Using Redis storage")
        except Exception as e:
            logger.warning(f"Redis init failed: {e}, using MemoryStorage")
    bot = Bot(token=config.BOT_TOKEN, request_timeout=60)
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(ActivityMiddleware())
    dp.include_routers(
        start.router,
        menu.router,
        browse.router,
        likes.router,
        profile.router,
        premium.router,
        report.router,
        admin.router,
        ai.router,
    )
    await on_startup()
    asyncio.create_task(inactivity_notifier())
    asyncio.create_task(fake_activity_simulator())
    if config.USE_WEBHOOK:
        # Здесь должен быть сервер для приёма вебхуков. Если его нет, рекомендуется выключить USE_WEBHOOK.
        logger.warning("Webhook mode enabled but no webhook server implemented. Falling back to polling.")
        # Для продакшена необходимо добавить aiohttp или FastAPI обработчик.
        # Пример см. в документации aiogram.
    else:
        logger.info("Starting polling...")
        await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())