# handlers/admin.py
from aiogram import types, Dispatcher
import plotly.express as px
from plotly import graph_objs as go
from plotly import io as pio
from sqlalchemy import select

from create_bot import bot
import io
import json
import os

from db_models import Player
from handlers.player_data import player_data_info
from src.guild import GuildData
from src.player import PlayerData
from src.utils import split_list, get_month_player_graphic
from settings import async_session_maker

COMMANDS = {
    "admin": "Получить информацию о доступных командах администратора",
    "add_player": "Записать нового игрока в базу (через пробел 3 значения - имя код_союзника тг_id)",
    "players_list": "Вывести все записи по игрокам (не стоит использовать в общих чатах)",
    "delete_player": "Удалить игрока из базы по имени",
    "graphic имя_игрока": "Выводит график сдачи игроком рейдовых купонов за все месяц",
    "guild_month": "Выводит график росто ГМ гильдии за месяц",
    "guild_year": "Выводит график роста ГМ гильдии за год",
    "refresh": "Экстреннее обновление базы данных"
    # Добавьте здесь другие команды по мере необходимости
}


async def admin_command_help(message: types.Message):
    """Выводит инфо о командах"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
            await bot.send_message(message.chat.id, f"Список доступных команд администратора:\n\n{commands}")
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def command_db_extra(message: types.Message):
    """Стартуем бот и обновляем БД"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            await bot.send_message(message.chat.id,
                                   "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
            await PlayerData().update_players_data()
            await GuildData().build_db()
        except Exception as e:
            print(e)
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def add_player(message: types.Message):
    """Добавляет игрока в ids.json"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            player_info = message.text.split(" ")
            if len(player_info) != 5:
                await bot.send_message(message.chat.id,
                                       f"Неверный формат команды. Используйте: \n/add_player имя код_союзника тг_id тг_ник\n Все через один пробел.")
                return
            # имя игрока, код и ID телеграма и ник в телеграме
            player_name, ally_code, tg_id, tg_nic = player_info[1], player_info[2], player_info[3], player_info[4]

            file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
            if os.path.exists(file_path):
                with open(file_path, "r") as json_file:
                    data = json.load(json_file)
                if len(data) >= 50:
                    await bot.send_message(message.chat.id, f"Превышено число членов гильдии. Добавление невозможно!")
                else:
                    # Добавление нового игрока в список
                    data.append({
                        ally_code: {
                            "player_name": player_name,
                            "tg_id": tg_id,
                            "tg_nic": tg_nic
                        }
                    })

                    # Запись обновленного списка в файл
                    with open(file_path, "w") as json_file:
                        json.dump(data, json_file, ensure_ascii=False)

                    await bot.send_message(message.chat.id, f"Игрок {player_name} был добавлен в список.")
            else:
                await bot.send_message(message.chat.id, "Файл ids.json не найден.")
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def players_list(message: types.Message):
    """Отправляет содержимое файла ids.json в чат"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
            if os.path.exists(file_path):
                with open(file_path, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                # Перебираем список игроков и формируем строку
                msg_list = []
                for index, player in enumerate(data):
                    for ally_code, info in player.items():
                        msg = (
                            f"{index + 1}: {info['player_name']}\n"
                            f"Код союзника: {ally_code}\n"
                            f"ID: {info['tg_id']}\n"
                            f"TG_NIC: {info['tg_nic']}\n"
                            f"{'-' * 30}\n"
                        )
                        msg_list.append(msg)
                msg_list.append(f"Всего: {len(data)}")
                final_lst_1, final_lst_2 = split_list(msg_list, 2)  # hfpltkztv
                # Соединяем все сообщения в одну большую строку
                final_msg_1 = ''.join(final_lst_1)
                final_msg_2 = ''.join(final_lst_2)

                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_1)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_2)
            else:
                await bot.send_message(message.chat.id, "Файл ids.json не найден.")
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def delete_player(message: types.Message):
    """Удаляет игрока из JSON файла"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            player_name = message.get_args()  # Получаем имя игрока
            if not player_name:
                await message.reply("Пожалуйста, предоставьте имя игрока.")
                return

            file_path = os.path.join(os.path.dirname(__file__), '../api/ids.json')

            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)

            player_found = False  # флаг, чтобы отслеживать, найден ли игрок

            for index, player in enumerate(data):
                for ally_code, info in player.items():
                    if info["player_name"] == player_name:
                        del data[index]  # Удаляем запись игрока
                        player_found = True  # отмечаем, что игрок найден
                        break

                if player_found:
                    break
            else:
                await message.reply("Игрок с таким именем не найден.")
                return

            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=2)

            await bot.send_message(message.chat.id, f"Игрок {player_name} удален из списка.")

        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def send_month_player_graphic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
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
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def send_month_guild_grafic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            image = await GuildData.get_guild_galactic_power(period="month")
            await bot.send_photo(chat_id=message.chat.id, photo=image)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def send_year_guild_grafic(message: types.Message):
    """Отправляет график рейда игрока"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        try:
            image = await GuildData.get_guild_galactic_power(period="year")
            await bot.send_photo(chat_id=message.chat.id, photo=image)
        except Exception as e:
            await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(command_db_extra, commands=['refresh'], is_chat_admin=True)
    dp.register_message_handler(add_player, commands=['add_player'], is_chat_admin=True)
    dp.register_message_handler(players_list, commands=['players_list'], is_chat_admin=True)
    dp.register_message_handler(delete_player, commands=['delete_player'], is_chat_admin=True)
    dp.register_message_handler(admin_command_help, commands=['admin'], is_chat_admin=True)
    dp.register_message_handler(send_month_player_graphic, commands=['graphic'], is_chat_admin=True)
    dp.register_message_handler(send_month_guild_grafic, commands=['guild_month'], is_chat_admin=True)
    dp.register_message_handler(send_year_guild_grafic, commands=['guild_year'], is_chat_admin=True)
