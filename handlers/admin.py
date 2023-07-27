# handlers/admin.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from create_bot import bot
import io
import json
import os

from src.graphics import get_month_player_graphic, get_guild_galactic_power
from src.guild import GuildData
from src.player import PlayerData
from src.utils import split_list, get_players_list_from_ids, add_player_to_ids, \
    delete_player_from_ids, check_guild_players, is_admin, is_super_admin

COMMANDS = {
    "admin": "Получить информацию о доступных командах администратора ⚙⚒",
    "group": "Сиквенция отправки групового сообщения",
    "group_all": "Сиквенция отправки сообщения всем",
    "players": "Сиквенция для записи/удаления  игрока в бот.\nЕсли нету тг ID или tg_nic то вместо пишите исключительно - null",
    "guild_month": "Выводит график ГМ гильдии за месяц",
    "guild_year": "Выводит график роста ГМ гильдии за год",
    "refresh": "Экстреннее обновление базы данных",

    "developer": "Получить информацию о доступных командах разработчика (Не влезай - убьет! ☠️)"
    # Добавьте здесь другие команды по мере необходимости
}


async def player_cmd_handler(call: types.CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Добавить игрока в бот", callback_data='add_player'))
    keyboard.add(types.InlineKeyboardButton("🗓 Список всех", callback_data='players_list'))
    keyboard.add(types.InlineKeyboardButton("🔪 Удалить игрока из бота", callback_data='delete_player'))
    await call.message.answer("Служба по игрокам", reply_markup=keyboard)


async def admin_command_help(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✍🏻 Отправить групповое сообщение", callback_data='group'))
    keyboard.add(types.InlineKeyboardButton("✉️ Отправить сообщение всем", callback_data='group_all'))
    keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Запись/удаление игрока в бот", callback_data='players'))
    keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за месяц", callback_data='guild_month'))
    keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за год", callback_data='guild_year'))
    keyboard.add(types.InlineKeyboardButton("🏗 Экстреннее обновление базы данных", callback_data='refresh'))
    keyboard.add(
        types.InlineKeyboardButton("☠️ Команды разработчика (Не влезай - убьет! ☠️", callback_data='developer'))
    await message.answer("Панель Администрации", reply_markup=keyboard)


# async def admin_command_help(message: types.Message):
#     """Выводит инфо о командах"""
#     is_guild_member = message.conf.get('is_guild_member', False)
#     admin = await is_admin(bot, message.from_user, message.chat)
#
#     if is_guild_member:
#         if admin:
#             try:
#                 commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
#                 await bot.send_message(message.chat.id, f"Список доступных команд администратора:\n\n{commands}")
#             except Exception as e:
#                 await message.reply(
#                     f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
#         else:
#             await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def command_db_extra(call: types.CallbackQuery, state: FSMContext):
    """Стартуем бот и обновляем БД"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    if is_guild_member:
        if admin:
            try:
                await bot.send_message(call.message.chat.id,
                                       "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
                await GuildData().build_db()
                await PlayerData().update_players_data()
            except Exception as e:
                print(e)
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def players_list(call: types.CallbackQuery, state: FSMContext):
    """Отправляет содержимое файла ids.json в чат"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    if is_guild_member:
        if admin:
            try:
                final_msg_1, final_msg_2 = await get_players_list_from_ids(call.message)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_1)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_2)

            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def send_month_guild_grafic(call: types.CallbackQuery, state: FSMContext):
    """Отправляет график мощи гильдии"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="month")
                await bot.send_photo(chat_id=call.message.chat.id, photo=image)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def send_year_guild_graphic(call: types.CallbackQuery, state: FSMContext):
    """Отправляет график рейда игрока"""
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="year")
                await bot.send_photo(chat_id=call.message.chat.id, photo=image)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def check_ids(call: types.CallbackQuery, state: FSMContext):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    if is_guild_member:
        if admin:
            try:
                await check_guild_players(call.message)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


def register_handlers_admin(dp: Dispatcher):
    dp.register_callback_query_handler(command_db_extra, text='refresh')
    dp.register_callback_query_handler(players_list, text=['players_list'], state='*')
    dp.register_message_handler(admin_command_help, commands=['admin'])
    dp.register_callback_query_handler(send_month_guild_grafic, text='guild_month')
    dp.register_callback_query_handler(send_year_guild_graphic, text='guild_year')
    dp.register_callback_query_handler(check_ids, text='check')
    dp.register_callback_query_handler(player_cmd_handler, text='players', state='*')
