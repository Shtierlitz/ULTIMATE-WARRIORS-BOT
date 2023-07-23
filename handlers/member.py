# handlers/member.py
import os

from aiogram.dispatcher import FSMContext
from sqlalchemy import select

from src.utils import gac_statistic, get_new_day_start
from src.player import PlayerData, PlayerScoreService, PlayerPowerService
from src.guild import GuildData
from create_bot import bot
from settings import async_session_maker
from aiogram import types, Dispatcher
import asyncio
from concurrent.futures import ThreadPoolExecutor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db_models import Player


GROUP_CHAT_ID = os.environ.get("GROUP_ID")
COMMANDS = {
    "start": "Получить информацию о доступных командах",
    "player": "Открыть панель кнопок где можно получить информацию по согильдийцу",
    "gac": "Получить полную статистику по регистрации на ВА с сылками на возможных соперников",
    "reid": "Контроль энки",
    "gp_all": "Список роста всей галактической мощи за календарный месяц",
    "guildinfo": "Инфа о гильдии",
    "admin": "Список команд администраторов",

    # Добавьте здесь другие команды по мере необходимости
}


def handle_exception(future):
    exception = future.exception()
    if exception:
        # здесь обработка исключения
        print(f"Ошибка:\n\n❌❌{exception}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


# Ваши обработчики
async def command_start(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            await bot.send_message(message.chat.id, f"Начинаем работу.")
            commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
            await bot.send_message(message.chat.id, f"Список доступных команд:\n\n{commands}")
        except Exception as e:
            print(e)
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def command_gac_statistic(message: types.Message):
    """Выводит инфо о ВА и ссылки на противников"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            await message.reply(f"Добываю статистику. Ожидайте выполнения...")
            st_1, st_2, st_3, st_4, st_5 = await gac_statistic()
            await bot.send_message(message.chat.id, text=st_1, parse_mode="Markdown")
            await bot.send_message(message.chat.id, text=st_2, parse_mode="Markdown")
            await bot.send_message(message.chat.id, text=st_3, parse_mode="Markdown")
            await bot.send_message(message.chat.id, text=st_4, parse_mode="Markdown")
            await bot.send_message(message.chat.id, text=st_5, parse_mode="Markdown")
        except Exception as e:
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_user_data(message: types.Message):
    """"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        player_name = message.text.split(maxsplit=1)[1]
        try:
            async with async_session_maker() as session:
                new_day_start = get_new_day_start()
                query = await session.execute(
                    select(Player).filter_by(name=player_name).filter(
                        Player.update_time >= new_day_start))
                player = query.scalars().first()
            player_str_list = await PlayerData().extract_data(player)
            await bot.send_message(message.chat.id, player_str_list)
        except Exception as e:
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_guild_info(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            guild_info = await GuildData.get_latest_guild_data()
            info_text = "\n".join(guild_info)
            await bot.send_message(message.chat.id, info_text)
        except Exception as e:
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_gp_all(message: types.Message):
    """Вся галактическая мощь за месяц по всем"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            message_strings = await PlayerPowerService.get_galactic_power_all()
            await bot.send_message(message.chat.id, message_strings)
        except Exception as e:
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")

def register_handlers_member(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(get_user_data, commands=['player1'], state='*', run_task=True)
    dp.register_message_handler(command_gac_statistic, commands=['gac'], state='*')
    dp.register_message_handler(get_gp_all, commands=['gp_all'], state='*')
    dp.register_message_handler(get_guild_info, commands=['guildinfo'])
