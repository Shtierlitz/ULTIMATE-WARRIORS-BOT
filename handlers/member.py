# handlers/member.py
import os

from aiogram.dispatcher import FSMContext
from sqlalchemy import select

from src.utils import gac_statistic, get_new_day_start
from src.player import PlayerData, PlayerScoreService
from src.guild import GuildData
from create_bot import bot
from settings import async_session_maker
from aiogram import types, Dispatcher
import asyncio
from concurrent.futures import ThreadPoolExecutor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db_models import Player
from worker.tasks import send_message

GROUP_CHAT_ID = os.environ.get("GROUP_ID")
COMMANDS = {
    "start": "Начать работу с ботом",
    "help": "Получить информацию о доступных командах",
    "player": "Открыть панель кнопок где можно получить информацию по согильдийцу",
    "gac": "Получить полную статистику по регистрации на ВА с сылками на возможных соперников",
    "reid_list": "Показывает полный список кто сколько купонов сдал",
    "reid_lazy": "Список тех кто еще не сдал 600",
    "reid_all": "Список сданной энки за все время"

    # Добавьте здесь другие команды по мере необходимости
}


# executor = ThreadPoolExecutor(max_workers=2)


def handle_exception(future):
    exception = future.exception()
    if exception:
        # здесь обработка исключения
        print(f"Ошибка: {exception}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


# async def command_start(message: types.Message):
#     """Стартуем бот и обновляем БД"""
#     await bot.send_message(message.chat.id, "Начинаем работу.\nОбновляем базу данных...\nПодождите...")
#     loop = asyncio.get_event_loop()
#     future = loop.run_in_executor(None, PlayerData().update_players_data)
#     # future.add_done_callback(handle_exception)
#     future2 = loop.run_in_executor(None, GuildData().build_db)
#     # future2.add_done_callback(handle_exception)
#     await bot.send_message(message.chat.id, "База данных обновляется в фоне.\nМожно приступать к работе.")

async def command_start(message: types.Message):
    """Стартуем бот и обновляем БД"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            await bot.send_message(message.chat.id,
                                   "Начинаем работу.\nОБаза данных обновляется в фоне.\nМожно приступать к работе.")
            await PlayerData().update_players_data()
            await GuildData().build_db()
        except Exception as e:
            print(e)
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


# Ваши обработчики
async def command_help(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
            await bot.send_message(message.chat.id, f"Список доступных команд:\n\n{commands}")

        except Exception as e:
            print(e)
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")



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
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


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
            player_str_list = PlayerData().extract_data(player)
            await bot.send_message(message.chat.id, player_str_list)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_raid_points(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            message_strings = await PlayerScoreService.get_raid_scores()
            await bot.send_message(message.chat.id, message_strings)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_raid_points_all(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            message_strings = await PlayerScoreService.get_raid_scores_all()
            await bot.send_message(message.chat.id, message_strings)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_raid_lazy(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            message_strings = await PlayerScoreService.get_reid_lazy_fools()
            await bot.send_message(message.chat.id, message_strings)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def register_handlers_member(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(command_help, commands=['help'])
    dp.register_message_handler(get_user_data, commands=['player1'], state='*', run_task=True)
    dp.register_message_handler(command_gac_statistic, commands=['gac'], state='*')
    dp.register_message_handler(get_raid_points, commands=['reid_list'], state='*')
    dp.register_message_handler(get_raid_lazy, commands=['reid_lazy'], state='*')
    dp.register_message_handler(get_raid_points_all, commands=['reid_all'], state='*')
