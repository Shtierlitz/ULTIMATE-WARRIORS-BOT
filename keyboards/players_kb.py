# keyboards/players_kb.py


from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy import func
from create_bot import session
from db_models import Player
from datetime import datetime, date


def create_keyboard():
    today = date.today()  # текущая дата
    # Запросить всех участников, которые были обновлены сегодня
    players = session.query(Player).filter(func.date(Player.update_time) == today).all()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.row(KeyboardButton("cencel"))  # Создать отдельную строку для кнопки "cencel"


    row_btns = []  # Создать список для кнопок строк

    for i, player in enumerate(players):
        button = KeyboardButton(f"/{player.name}")  # Создать кнопку с именем игрока
        row_btns.append(button)  # Добавить кнопку в список кнопок для строки
        if (i + 1) % 2 == 0:  # Если количество кнопок в строке достигло 4
            keyboard.row(*row_btns)  # Добавить строку кнопок на клавиатуру
            row_btns = []  # Очистить список кнопок для строки
    if row_btns:  # Если есть оставшиеся кнопки
        keyboard.row(*row_btns)  # Добавить оставшиеся кнопки на клавиатуру

    return keyboard


def create_player_info_keyboard(player_name: str):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    today = date.today()  # текущая дата
    player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
    if player:
        keyboard.row(KeyboardButton("back"), KeyboardButton("cencel")) # Создать отдельную строку для кнопки "cencel"
        keyboard.row(KeyboardButton("all_data"))

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

