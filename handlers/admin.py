# handlers/admin.py

import io
import os
from pprint import pprint

from aiogram import types, Dispatcher

from create_bot import bot
from src.decorators import (
    member_admin_check,
    member_super_admin_check
)
from src.graphics import get_guild_galactic_power
from src.guild import GuildData
from src.player import PlayerData, PlayerService
from src.roster_unit_service import RosterDataService
from src.uint import UnitAggregateService
from src.utils import (
    get_players_list_from_ids,
    check_guild_players,
    is_admin
)


@member_super_admin_check
async def player_cmd_handler(call: types.CallbackQuery):
    """Меню добавления/удаления игрока в бот"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Добавить игрока в бот", callback_data='add_player'))
    keyboard.add(types.InlineKeyboardButton("🗓 Список всех", callback_data='players_list'))
    keyboard.add(types.InlineKeyboardButton("🔪 Удалить игрока из бота", callback_data='delete_player'))
    await call.message.answer("👮🏻‍♂️ Служба по игрокам", reply_markup=keyboard)


async def admin_command_help(update: [types.Message, types.CallbackQuery]):
    if isinstance(update, types.Message):
        user_id = update.from_user.id
        chat_id = update.chat.id
        message_or_call = update
    elif isinstance(update, types.CallbackQuery):
        user_id = update.from_user.id
        chat_id = update.message.chat.id
        message_or_call = update.message
    else:
        # Неизвестный тип обновления, выходим из функции
        return

    is_guild_member = message_or_call.conf.get('is_guild_member', False)
    admin = await is_admin(bot, user_id, chat_id)
    if is_guild_member:
        if admin:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("✍🏻 Групповое сообщение", callback_data='group'))
            keyboard.add(types.InlineKeyboardButton("✉️ Сообщение всем", callback_data='group_all'))
            keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Запись/удаление игрока в бот", callback_data='players'))
            keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за месяц", callback_data='guild_month'))
            keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за год", callback_data='guild_year'))
            keyboard.add(types.InlineKeyboardButton("🏗 Экстреннее обновление БД", callback_data='refresh'))
            keyboard.add(types.InlineKeyboardButton("🏗 Экстреннее обновление юнитов", callback_data='refresh_units'))
            keyboard.add(types.InlineKeyboardButton("📊 Проверка все ли игроки в базе", callback_data='check_ids'))
            keyboard.add(types.InlineKeyboardButton("🔍 Найти юнит", callback_data='find_unit'))
            keyboard.add(
                types.InlineKeyboardButton("☠️ Команды разработчика ☠️", callback_data='developer'))
            await message_or_call.answer("👮🏻‍♂️ Админ панель 👮🏻", reply_markup=keyboard)
            # pprint(await RosterDataService().get_russian_localized_unit_name('BOBAFETT')
            # data_1 = await PlayerService().get_comlink_data()
            await PlayerService().update_localization_data()
            # data_2 = await PlayerService().get_comlink_stat_mod_data()
            # pprint(data_2)
            # for i in data_2:
            #     if i['id'] == 451:
            #         pprint(i)
            # print('not found')
        else:
            await message_or_call.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await message_or_call.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


@member_admin_check
async def command_unit_db_extra(call: types.CallbackQuery):
    """Стартуем бот и обновляем БД"""
    await bot.send_message(call.message.chat.id,
                           "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
    await UnitAggregateService().create_or_update_unit()


@member_admin_check
async def command_db_extra(call: types.CallbackQuery):
    """Стартуем бот и обновляем БД"""
    await bot.send_message(call.message.chat.id,
                           "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
    await GuildData().build_db()
    await PlayerData().update_players_data()


@member_admin_check
async def command_check_ids(call: types.CallbackQuery):
    """Проверяем все ли игроки в ids.json"""
    await PlayerData().check_members_in_ids(call)
    await PlayerData().check_ids_in_guild(call)


@member_admin_check
async def players_list(call: types.CallbackQuery):
    """Отправляет содержимое файла ids.json в чат"""
    final_msg_1, final_msg_2 = await get_players_list_from_ids(call.message)
    await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_1)
    await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_2)


@member_admin_check
async def send_month_guild_grafic(call: types.CallbackQuery):
    """Отправляет график мощи гильдии"""
    image: io.BytesIO = await get_guild_galactic_power(period="month")
    await bot.send_photo(chat_id=call.message.chat.id, photo=image)


@member_admin_check
async def send_year_guild_graphic(call: types.CallbackQuery):
    """Отправляет график рейда игрока"""
    image: io.BytesIO = await get_guild_galactic_power(period="year")
    await bot.send_photo(chat_id=call.message.chat.id, photo=image)


@member_admin_check
async def check_ids(call: types.CallbackQuery):
    """Делает проверку всех внесенных в ids.json на доступность"""
    await check_guild_players(call.message)


def register_handlers_admin(dp: Dispatcher):
    dp.register_callback_query_handler(command_db_extra, text='refresh')
    dp.register_callback_query_handler(command_unit_db_extra, text='refresh_units')
    dp.register_callback_query_handler(command_check_ids, text='check_ids')
    dp.register_callback_query_handler(players_list, text=['players_list'], state='*')
    dp.register_callback_query_handler(admin_command_help, text='admin')
    dp.register_message_handler(admin_command_help, commands='admin')
    dp.register_callback_query_handler(send_month_guild_grafic, text='guild_month')
    dp.register_callback_query_handler(send_year_guild_graphic, text='guild_year')
    dp.register_callback_query_handler(check_ids, text='check_ids')
    dp.register_callback_query_handler(player_cmd_handler, text='players', state='*')
