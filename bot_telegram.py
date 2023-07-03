# bot_telegram.py


from aiogram.utils import executor

import db
from handlers import member, admin, other, player_data
# from data_base import sqlite_db
from create_bot import dp


async def on_startup(_):  # функция настроек старта бота.
    print("Бот вышел в онлайн")  # Выводит в консоль в файле bat
    # необходимо подключить в executor.start_polling
    session = db.Session()


member.register_handlers_member(dp)  # регистрация хендлеров
player_data.register_handlers_player(dp)
# admin.register_handlers_admin(dp)
# other.register_handlers_other(dp)  # хендлеры без команд нужно импортировать последними

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup)  # нужно чтоб не завалило спамом когда он не активный
