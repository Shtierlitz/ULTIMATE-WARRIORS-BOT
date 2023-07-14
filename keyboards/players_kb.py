# keyboards/players_kb.py


from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy import func, select

from db_models import Player
from datetime import datetime, date

from settings import async_session_maker
from src.utils import get_new_day_start


async def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    new_day_start = get_new_day_start()

    async with async_session_maker() as session:
        query = await session.execute(
            select(Player.name).filter(Player.update_time >= new_day_start)
        )
        players = query.scalars().all()

    if players:
        keyboard.row(KeyboardButton("cancel"))

        row_btns = []  # Создать список для кнопок строк
        for index, player in enumerate(players):
            button = KeyboardButton(player)  # Создать кнопку с именем игрока
            row_btns.append(button)
            if (index + 1) % 2 == 0:  # Если это каждая 2-ая кнопка
                keyboard.row(*row_btns)  # Добавить ряд кнопок на клавиатуру
                row_btns = []  # Очистить список кнопок для следующего ряда

        if row_btns:  # Если есть оставшиеся кнопки
            keyboard.row(*row_btns)  # Добавить оставшиеся кнопки на клавиатуру

    return keyboard



async def create_player_info_keyboard(player_name: str):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    new_day_start = get_new_day_start()
    async with async_session_maker() as session:
        query = await session.execute(
            select(Player).filter(Player.update_time >= new_day_start, Player.name == player_name))
        player = query.scalars().first()

    # player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
    if player:
        keyboard.row(KeyboardButton("back"), KeyboardButton("cencel")) # Создать отдельную строку для кнопки "cencel"
        keyboard.row(KeyboardButton("all_data"))
        keyboard.row(KeyboardButton("GP_month"), KeyboardButton("GP_year"))

        row_btns = []  # Создать список для кнопок строк

        for index, column in enumerate(Player.__table__.columns):  # Получить все поля модели Player
            if column.name in ('name', 'tg_id', 'id'):  # Если имя поля 'tg_id', пропустите его
                continue
            button = KeyboardButton(column.name)  # Создать кнопку с именем поля
            row_btns.append(button)
            if (index + 1) % 2 == 0:  # Если это каждая 4-ая кнопка
                keyboard.row(*row_btns)  # Добавить ряд кнопок на клавиатуру
                row_btns = []  # Очистить список кнопок для следующего ряда

        if row_btns:  # Если есть оставшиеся кнопки
            keyboard.row(*row_btns)  # Добавить оставшиеся кнопки на клавиатуру

    return keyboard

