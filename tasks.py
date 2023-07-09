# tasks.py

from telegram import Bot
from celery import shared_task

bot = Bot(token='YOUR_BOT_TOKEN')

@shared_task
def send_message(user_id, message):
    bot.sendMessage(chat_id=user_id, text=message)  # Замените 'send_message' на 'sendMessage'

