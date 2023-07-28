# handlers/member.py
import os

from aiogram.dispatcher import FSMContext
from sqlalchemy import select

from src.utils import gac_statistic, get_new_day_start, is_admin
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


async def command_start(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🫵🏻 Инфа по игрокам", callback_data='player'))
            keyboard.add(types.InlineKeyboardButton("⚔️ Статистика ВА по всем", callback_data='gac'))
            keyboard.add(types.InlineKeyboardButton("🔋 Контроль энки", callback_data='reid'))
            keyboard.add(types.InlineKeyboardButton("💪🏻 ГМ по всем за месяц", callback_data='gp_all'))
            keyboard.add(types.InlineKeyboardButton("🏛 Инфа о гильдии", callback_data='guildinfo'))
            keyboard.add(types.InlineKeyboardButton("👮🏻‍♂️ Команды админов", callback_data='admin'))
            await message.answer("🧑🏻‍🌾 Панель Пользователей 👨🏻‍🌾", reply_markup=keyboard)
        except Exception as e:
            print(e)
            await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def command_gac_statistic(call: types.CallbackQuery):
    """Выводит инфо о ВА и ссылки на противников"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            await call.message.reply(f"Добываю статистику. Ожидайте выполнения...")
            st_1, st_2, st_3, st_4, st_5 = await gac_statistic()
            await bot.send_message(call.message.chat.id, text=st_1, parse_mode="Markdown")
            await bot.send_message(call.message.chat.id, text=st_2, parse_mode="Markdown")
            await bot.send_message(call.message.chat.id, text=st_3, parse_mode="Markdown")
            await bot.send_message(call.message.chat.id, text=st_4, parse_mode="Markdown")
            await bot.send_message(call.message.chat.id, text=st_5, parse_mode="Markdown")
        except Exception as e:
            await call.message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

# async def get_user_data(call: types.CallbackQuery):
#     """"""
#     is_guild_member = call.message.conf.get('is_guild_member', False)
#     if is_guild_member:
#         player_name = call.message.text.split(maxsplit=1)[1]
#         try:
#             async with async_session_maker() as session:
#                 new_day_start = get_new_day_start()
#                 query = await session.execute(
#                     select(Player).filter_by(name=player_name).filter(
#                         Player.update_time >= new_day_start))
#                 player = query.scalars().first()
#             player_str_list = await PlayerData().extract_data(player)
#             await bot.send_message(call.message.chat.id, player_str_list)
#         except Exception as e:
#             await call.message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def get_guild_info(call: types.CallbackQuery):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            guild_info = await GuildData.get_latest_guild_data()
            info_text = "\n".join(guild_info)
            await bot.send_message(call.message.chat.id, info_text)
        except Exception as e:
            await call.message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def get_gp_all(call: types.CallbackQuery):
    """Вся галактическая мощь за месяц по всем"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            message_strings = await PlayerPowerService.get_galactic_power_all()
            await bot.send_message(call.message.chat.id, message_strings)
        except Exception as e:
            await call.message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

def register_handlers_member(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    # dp.register_message_handler(get_user_data, text='player1', state='*', run_task=True)
    dp.register_callback_query_handler(command_gac_statistic, text='gac', state='*')
    dp.register_callback_query_handler(get_gp_all, text='gp_all', state='*')
    dp.register_callback_query_handler(get_guild_info, text='guildinfo')
