# middlewares/user_check.py

from aiogram.dispatcher import FSMContext
import json
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware


# Загрузите ids.json в память
with open("./api/ids.json") as f:
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
        if message.text.startswith('/') and not is_guild_member:
            await message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")
            return False



