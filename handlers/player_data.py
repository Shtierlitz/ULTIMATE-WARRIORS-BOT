# handlers/player_data.py

from aiogram import types, Dispatcher

from create_bot import session
from keyboards.players_kb import create_keyboard, create_player_info_keyboard
from sqlalchemy import func
from datetime import date
from db_models import Player


async def player_buttons(message: types.Message):
    try:
        kb = create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def player_info_buttons(message: types.Message):
    player_name = message.text[1:]  # Удалить символ '/' перед именем игрока
    today = date.today()  # текущая дата
    player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
    if not player:  # Если игрока с таким именем нет в базе данных
        return  # Игнорировать сообщение
    kb = create_player_info_keyboard(player_name)  # Создать клавиатуру
    await message.reply(f"Выберете информацию об игроке {player_name}.",
                        reply_markup=kb)  # Отправить сообщение с клавиатурой


def register_handlers_player(dp: Dispatcher):
    dp.register_message_handler(player_buttons, commands=['player'])
    dp.register_message_handler(player_info_buttons, content_types=types.ContentType.TEXT)
