# bot_telegram.py

import os

from apscheduler.triggers.cron import CronTrigger

import apsched
import settings
from aiogram.utils import executor
from handlers import member, admin, player_data, send_group_message, developer, send_message_everyone, add_player_state
from create_bot import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import logging

load_dotenv()


async def on_startup(_):  # функция настроек старта бота.
    print("Бот вышел в онлайн")
    logging.info("Бот вышел в онлайн")
    # await settings.create_tables()
    scheduler = AsyncIOScheduler(timezone=os.environ.get("TIME_ZONE", "UTC"))
    scheduler.add_job(apsched.check_guild_points, 'cron', hour=int(os.environ.get("REMIND_GUILD_POINTS_HOUR", 14)),
                      minute=int(os.environ.get("REMIND_GUILD_POINTS_MINUTES", 30)),
                      timezone=os.environ.get("TIME_ZONE", "UTC"))
    scheduler.add_job(apsched.update_db, trigger='interval', minutes=5)
    # Добавляем задачу, которая будет запускаться в последний день каждого месяца в выбранное время в .env или в 16:20
    scheduler.add_job(apsched.final_points_per_month, 'cron',
                      hour=int(os.environ.get("REMIND_LAST_MONTH_POINTS_HOUR", 16)),
                      minute=int(os.environ.get("REMIND_LAST_MONTH_POINTS_MINUTES", 25)))
    scheduler.add_job(apsched.final_gp_per_month, 'cron',
                      hour=int(os.environ.get("REMIND_LAST_MONTH_POINTS_HOUR", 16)),
                      minute=int(os.environ.get("REMIND_LAST_MONTH_POINTS_MINUTES", 25)))

    scheduler.start()


member.register_handlers_member(dp)  # регистрация хендлеров
player_data.register_handlers_player(dp)
add_player_state.register_handlers_add_player(dp)
send_group_message.register_handlers_group_message(dp)
send_message_everyone.register_handlers_message_all(dp)

admin.register_handlers_admin(dp)
developer.register_handlers_developer(dp)

if __name__ == '__main__':
    # while True:
    #     try:

    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup)  # нужно чтоб не завалило спамом когда он не активный

    # except NetworkError as e:
    #     print(f"Произошла ошибка сервера: {e}")
    #     continue
