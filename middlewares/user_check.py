# middlewares/user_check.py
import os

from aiogram.dispatcher import FSMContext
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

        # проверяем, является ли сообщение командой и не является ли отправитель членом гильдии
        if message.text and message.text.startswith('/') and not is_guild_member:
            await message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")
            return False


