# middlewares/user_check.py

import os

import json
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware


# Получить путь к текущему файлу
current_file_path = os.path.realpath(__file__)
# Получить путь к каталогу текущего файла
current_dir_path = os.path.dirname(current_file_path)
# Сформировать путь к ids.json
ids_file_path = os.path.join(current_dir_path, '..', os.environ.get('IDS_JSON'))

# Загрузить ids.json в память
with open(ids_file_path) as f:
    guild_members = json.load(f)


# Определите middleware
class GuildMembershipMiddleware(BaseMiddleware):
    """Не позволяет пользоваться ботом никому кроме тех кто дал tg_id"""
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = str(message.from_user.id)
        is_guild_member = any(user_id in member.values() for dictionary in guild_members for member in dictionary.values())
        # сохраняем данные в message.conf
        message.conf['is_guild_member'] = is_guild_member
        # Вывод ID мне в личку если в .env True
        if os.environ.get("SEND_ID"):
            await send_id(message)
        # проверяем, является ли сообщение командой и не является ли отправитель членом гильдии
        if message.text and message.text.startswith('/') and not is_guild_member:
            await message.answer(
                "❌ Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Команда запрещена.\n"
                "👉🏻 Для вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")
            return False

    async def on_pre_process_callback_query(self, call: types.CallbackQuery, data: dict):
        user_id = str(call.from_user.id)
        is_guild_member = any(user_id in member.values() for dictionary in guild_members for member in dictionary.values())
        # сохраняем данные в call.message.conf
        call.message.conf['is_guild_member'] = is_guild_member


async def send_id(message: types.Message):
    # Получить путь к текущему файлу
    current_file_path = os.path.realpath(__file__)
    # Получить путь к каталогу текущего файла
    current_dir_path = os.path.dirname(current_file_path)
    # Сформировать путь к ids.json
    ids_file_path = os.path.join(current_dir_path, '..', os.environ.get('IDS_JSON'))

    # Загрузить ids.json в память
    with open(ids_file_path) as f:
        guild_members = json.load(f)

    my_chat_id = int(os.environ.get('MY_ID'))
    user_id = str(message.from_user.id)

    # Найти player_name по user_id
    player_name = None
    for dictionary in guild_members:
        for player_data in dictionary.values():
            if player_data.get('tg_id') == user_id:
                player_name = player_data.get('player_name')
                break

    if player_name:
        print(my_chat_id, f"ID пользователя: {user_id}, Имя игрока: {player_name}")
    else:
        print(my_chat_id, f"ID пользователя: {user_id} не найден в guild_members.")