.PHONY: help run migrate shell

help:
	@echo "Available commands:"
	@echo "  make run        - Start the bot (polling mode)"
	@echo "  make migrate    - Run Alembic migrations (if set up)"
	@echo "  make shell      - Open a Python shell with app context"

run:
	python bot.py

migrate:
	alembic upgrade head

shell:
	python -c "import asyncio; from database.db import async_session; from database.models import *; print('Ready')"