# bot_telegram.py
import os
from datetime import datetime, timedelta

from aiogram.utils import executor

import apsched
import settings
from handlers import member, admin, player_data, send_group_message

from create_bot import dp, bot
# from worker.celery_app import app  # нужно чтобы бот увидел брокер НЕ УДАЛЯТЬ
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()


async def on_startup(_):  # функция настроек старта бота.
    print("Бот вышел в онлайн")
    await settings.create_tables()
    scheduler = AsyncIOScheduler(timezone=os.environ.get("TIME_ZONE", "UTC"))
    scheduler.add_job(apsched.check_guild_points, 'cron', hour=int(os.environ.get("REMIND_GUILD_POINTS_HOUR", 14)),
                      minute=int(os.environ.get("REMIND_GUILD_POINTS_MINUTES", 30)),
                      timezone=os.environ.get("TIME_ZONE", "UTC"))
    scheduler.add_job(apsched.update_db, trigger='interval', minutes=5)

    scheduler.start()


member.register_handlers_member(dp)  # регистрация хендлеров
player_data.register_handlers_player(dp)
send_group_message.register_handlers_group_message(dp)
admin.register_handlers_admin(dp)

# other.register_handlers_other(dp)  # хендлеры без команд нужно импортировать последними

if __name__ == '__main__':
    # while True:
    #     try:

    # send_message.delay(562272797, "Hello There")
    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup)  # нужно чтоб не завалило спамом когда он не активный

    # except NetworkError as e:
    #     print(f"Произошла ошибка сервера: {e}")
    #     continue
