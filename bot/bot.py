import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from database.db import engine, Base, AsyncSessionLocal
from handlers import start, menu, browse, likes, chats, profile, premium, report, admin

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

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created (if not exist).")

async def main():
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
    
    # Создаём бота, передавая таймаут напрямую (без DefaultBotProperties)
    bot = Bot(token=config.BOT_TOKEN, request_timeout=60)
    
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DBSessionMiddleware())
    dp.include_routers(
        start.router,
        menu.router,
        browse.router,
        likes.router,
        chats.router,
        profile.router,
        premium.router,
        report.router,
        admin.router,
    )
    await on_startup()
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