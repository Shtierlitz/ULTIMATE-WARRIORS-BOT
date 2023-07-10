# worker/tasks.py
from celery import shared_task
import asyncio


from create_bot import bot, dp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

@shared_task
def send_message(user_id, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(dp.bot.send_message(chat_id=user_id, text=message))
    except Exception as e:
        logging.error(e)
        print(f"Exception occurred: {e}")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()






