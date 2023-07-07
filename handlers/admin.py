# handlers/admin.py
from aiogram import types, Dispatcher

from create_bot import bot

import json
import os

COMMANDS = {
    "admin": "Получить информацию о доступных командах администратора",
    "add_player": "Записать нового игрока в базу (через пробел 3 значения - имя код_союзника тг_id)",
    "players_list": "Вывести все записи по игрокам (не стоит использовать в общих чатах)",
    "delete_player": "Удалить игрока из базы по имени"
    # Добавьте здесь другие команды по мере необходимости
}


async def admin_command_help(message: types.Message):
    """Выводит инфо о командах"""
    try:
        commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
        await bot.send_message(message.chat.id, f"Список доступных команд администратора:\n\n{commands}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def add_player(message: types.Message):
    """Добавляет игрока в ids.json"""
    try:
        player_info = message.text.split(" ")
        if len(player_info) != 4:
            await bot.send_message(message.chat.id,
                                   f"Неверный формат команды. Используйте: /add_player Имя Ally_code Tg_id")
            return

        # имя игрока, код и ID телеграмма
        player_name, ally_code, tg_id = player_info[1], player_info[2], player_info[3]

        file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
        if os.path.exists(file_path):
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
            if len(data) >= 50:
                await bot.send_message(message.chat.id, f"Превышено число членов гильдии. Добавление невозможно!")
            else:
                # Добавление нового игрока в список
                data.append({
                    player_name: {
                        "ally_code": ally_code,
                        "tg_id": tg_id
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
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as json_file:
                data = json.load(json_file)

            # Перебираем список игроков и формируем строку
            msg_list = []
            for player in data:
                for name, info in player.items():
                    msg = (
                        f"Имя: {name}\n"
                        f"Код союзника: {info['ally_code']}\n"
                        f"ID: {info['tg_id']}\n"
                        f"{'-' * 30}\n"
                    )
                    msg_list.append(msg)
            msg_list.append(f"Всего: {len(data)}")
            # Соединяем все сообщения в одну большую строку
            final_msg = ''.join(msg_list)

            await bot.send_message(message.chat.id, final_msg)
        else:
            await bot.send_message(message.chat.id, "Файл ids.json не найден.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def delete_player(message: types.Message):
    """Удаляет игрока из JSON файла"""
    try:
        player_name = message.get_args()  # Получаем имя игрока
        if not player_name:
            await message.reply("Пожалуйста, предоставьте имя игрока.")
            return

        file_path = os.path.join(os.path.dirname(__file__), '../api/ids.json')

        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        for index, player in enumerate(data):
            if player_name in player:
                del data[index]  # Удаляем запись игрока
                break
        else:
            await message.reply("Игрок с таким именем не найден.")
            return

        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2)

        await bot.send_message(message.chat.id, f"Игрок {player_name} удален из списка.")

    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(add_player, commands=['add_player'], is_chat_admin=True)
    dp.register_message_handler(players_list, commands=['players_list'], is_chat_admin=True)
    dp.register_message_handler(delete_player, commands=['delete_player'], is_chat_admin=True)
    dp.register_message_handler(admin_command_help, commands=['admin'], is_chat_admin=True)
