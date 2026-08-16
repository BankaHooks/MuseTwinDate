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
from handlers import start, menu, browse, likes, profile, premium, report, admin
from handlers import ai

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
            tg_user = getattr(event.event, "from_user", None)
            if tg_user:
                data["user"] = await crud.get_user_by_telegram_id(session, tg_user.id)
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
    if config.USE_WEBHOOK:
        await bot.set_webhook(
            url=config.WEBHOOK_URL,
            secret_token=config.WEBHOOK_SECRET
        )
        logger.info(f"Webhook set to {config.WEBHOOK_URL}")
    else:
        logger.info("Starting polling...")
        await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())