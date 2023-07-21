# handlers/admin.py
from aiogram import types, Dispatcher

from create_bot import bot
import io
import json
import os

from src.graphics import get_month_player_graphic, get_guild_galactic_power
from src.guild import GuildData
from src.player import PlayerData
from src.utils import split_list, get_players_list_from_ids, add_player_to_ids, \
    delete_player_from_ids, check_guild_players, is_admin

COMMANDS = {
    "admin": "Получить информацию о доступных командах администратора ⚙⚒",
    "group": "Сиквенция отправки групового сообщения",
    "group_all": "Сиквенция отправки сообщения всем",
    "add_player": "Сиквенция для записи нового игрока в базу.\nЕсли нету тг ID или tg_nic то вместо пишите исключительно - null",
    "players_list": "Вывести все записи по игрокам (не стоит использовать в общих чатах)",
    "delete_player": "Удалить игрока из базы по имени",
    "graphic имя_игрока": "Выводит график сдачи игроком рейдовых купонов за все месяц",
    "guild_month": "Выводит график росто ГМ гильдии за месяц",
    "guild_year": "Выводит график роста ГМ гильдии за год",
    "refresh": "Экстреннее обновление базы данных",
    "check": "Проверка всех пользователей на доступность для бота",
    "developer": "Получить информацию о доступных командах разработчика (Не влезай - убьет! ☠️)"
    # Добавьте здесь другие команды по мере необходимости
}


async def admin_command_help(message: types.Message):
    """Выводит инфо о командах"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
                await bot.send_message(message.chat.id, f"Список доступных команд администратора:\n\n{commands}")
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def command_db_extra(message: types.Message):
    """Стартуем бот и обновляем БД"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                await bot.send_message(message.chat.id,
                                       "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
                await GuildData().build_db()
                await PlayerData().update_players_data()
            except Exception as e:
                print(e)
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def players_list(message: types.Message):
    """Отправляет содержимое файла ids.json в чат"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                final_msg_1, final_msg_2 = await get_players_list_from_ids(message)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_1)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_2)

            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def delete_player(message: types.Message):
    """Удаляет игрока из JSON файла"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                await delete_player_from_ids(message)
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def send_month_player_graphic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                player_name = message.get_args()
                if not player_name:
                    await message.reply(f"Неверный формат ввода. Правильно:\n/grafic имя_игрока\nЧерез пробел.")
                    return
                if "@" in player_name:
                    player_name = player_name.replace("@", "")
                buf: io.BytesIO = await get_month_player_graphic(message, player_name)
                if buf:
                    await bot.send_photo(chat_id=message.chat.id, photo=buf)
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"Неверно введено имя \"{player_name}\". Попробуйте проверить правильность написания")
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def send_month_guild_grafic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="month")
                await bot.send_photo(chat_id=message.chat.id, photo=image)
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def send_year_guild_grafic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="year")
                await bot.send_photo(chat_id=message.chat.id, photo=image)
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


async def check_ids(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    if is_guild_member:
        if admin:
            try:
                await check_guild_players(message)
            except Exception as e:
                await message.reply(f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(command_db_extra, commands=['refresh'], is_chat_admin=True)
    dp.register_message_handler(players_list, commands=['players_list'], is_chat_admin=True)
    dp.register_message_handler(delete_player, commands=['delete_player'], is_chat_admin=True)
    dp.register_message_handler(admin_command_help, commands=['admin'])
    dp.register_message_handler(send_month_player_graphic, commands=['graphic'], is_chat_admin=True)
    dp.register_message_handler(send_month_guild_grafic, commands=['guild_month'], is_chat_admin=True)
    dp.register_message_handler(send_year_guild_grafic, commands=['guild_year'], is_chat_admin=True)
    dp.register_message_handler(check_ids, commands=['check'], is_chat_admin=True)
