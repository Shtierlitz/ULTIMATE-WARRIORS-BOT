# worker/celery_app.py

import asyncio
from celery import Celery

celery_event_loop = asyncio.new_event_loop()


# Создание Celery приложения
app = Celery(main="tg_bot", broker='redis://localhost:6379/0')
app.autodiscover_tasks()
from worker.tasks import send_message
app.conf.broker_connection_retry_on_startup = True
