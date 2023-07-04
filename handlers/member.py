# handlers/member.py
import os

from api_utils import extract_data, update_players_data
from create_bot import bot, session
from aiogram import types, Dispatcher
import asyncio
from concurrent.futures import ThreadPoolExecutor

from db_models import Player

GROUP_CHAT_ID = os.environ.get("GROUP_ID")
COMMANDS = {
    "start": "Начать работу с ботом",
    "help": "Получить информацию о доступных командах",
    "player": "Открыть панель кнопок где можно получить информацию по согильдийцу"
    # Добавьте здесь другие команды по мере необходимости
}

executor = ThreadPoolExecutor(max_workers=1)


async def command_start(message: types.Message):
    """Стартуем бот и обновляем БД"""
    try:
        await bot.send_message(message.chat.id, "Начинаем работу.\nОбновляем базу данных...\nПодождите...")
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, update_players_data)
        await bot.send_message(message.chat.id, "База данных обновляется в фоне.\nМожно приступать к работе.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def command_help(message: types.Message):
    """Выводит инфо о командах"""
    try:
        commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
        await bot.send_message(message.chat.id, f"Список доступных команд:\n\n{commands}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_user_data(message: types.Message):
    """"""
    player_name = message.text.split(maxsplit=1)[1]
    print(player_name)
    try:
        player = session.query(Player).filter_by(name=player_name).first()
        player_str_list = extract_data(player)
        await bot.send_message(message.chat.id, player_str_list)
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def register_handlers_member(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(command_help, commands=['help'])
    dp.register_message_handler(get_user_data, commands=['player1'], state='*', run_task=True)
