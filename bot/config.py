import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./muse_twin_date.db")
    REDIS_URL = os.getenv("REDIS_URL")
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "False").lower() == "true"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    MEDIA_DIR = "media"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
config = Config()