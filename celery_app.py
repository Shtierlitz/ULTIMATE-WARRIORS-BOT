# celery_app.py


from celery import Celery

# Создание Celery приложения
app = Celery('tasks', broker='redis://localhost:6379/0')
from tasks import send_message
app.conf.broker_connection_retry_on_startup = True