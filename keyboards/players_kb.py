# keyboards/players_kb.py


from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy import func, select

from db_models import Player
from datetime import datetime, date

from settings import async_session_maker
from src.utils import get_new_day_start, get_player_by_name_or_nic


async def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    new_day_start = get_new_day_start()

    async with async_session_maker() as session:
        query = await session.execute(
            select(Player).filter(Player.update_time >= new_day_start)
        )
        players = query.scalars().all()



    if players:
        keyboard.row(KeyboardButton("Отмена❌"))

        row_btns = []  # Создать список для кнопок строк
        for index, player in enumerate(sorted(players, key=lambda p: p.name)):
            button = KeyboardButton(player.name)  # Создать кнопку с именем игрока
            row_btns.append(button)
            if (index + 1) % 2 == 0:  # Если это каждая 2-ая кнопка
                keyboard.row(*row_btns)  # Добавить ряд кнопок на клавиатуру
                row_btns = []  # Очистить список кнопок для следующего ряда

        if row_btns:  # Если есть оставшиеся кнопки
            keyboard.row(*row_btns)  # Добавить оставшиеся кнопки на клавиатуру

    return keyboard



async def create_player_info_keyboard(player_name: str):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    player = await get_player_by_name_or_nic(player_name)

    if player:
        keyboard.row(KeyboardButton("🔙Назад"), KeyboardButton("Отмена❌")) # Создать отдельную строку для кнопки "cencel"
        keyboard.row(KeyboardButton("🗒Все данные"))
        keyboard.row(KeyboardButton("📊 ГМ за месяц"), KeyboardButton("📊 ГМ за год"))
        keyboard.row(KeyboardButton("📊 пешки за месяц"), KeyboardButton("📊 флота за месяц"))
        keyboard.row(KeyboardButton("📊 пешки за год"), KeyboardButton("📊 флота за год"))

        # row_btns = []  # Создать список для кнопок строк
        #
        # for index, column in enumerate(Player.__table__.columns):  # Получить все поля модели Player
        #     if column.name in ('name', 'tg_id', 'id'):  # Если имя поля 'tg_id', пропустите его
        #         continue
        #     button = KeyboardButton(column.name)  # Создать кнопку с именем поля
        #     row_btns.append(button)
        #     if (index + 1) % 2 == 0:  # Если это каждая 4-ая кнопка
        #         keyboard.row(*row_btns)  # Добавить ряд кнопок на клавиатуру
        #         row_btns = []  # Очистить список кнопок для следующего ряда
        #
        # if row_btns:  # Если есть оставшиеся кнопки
        #     keyboard.row(*row_btns)  # Добавить оставшиеся кнопки на клавиатуру

    return keyboard

