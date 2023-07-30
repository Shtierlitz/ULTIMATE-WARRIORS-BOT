# handlers/developer.py

from aiogram import types, Dispatcher
from src.utils import is_member_admin_super

COMMANDS = {
    "del_player_db <имя игрока или ник или код союзника>":
        "Удаляет все записи из базы данных об игроке.\nИспользовать "
        "только если игрок покинул гильдию и больше записи о нем не представляют "
        "ценности!\nОбратного эффекта команда не имеет!☠️☠️☠️",
    "check": "Проверка всех пользователей на доступность для бота",

    # Добавьте здесь другие команды по мере необходимости
}


async def developer_commands(call: types.CallbackQuery):
    """Выводит инфо о командах разработчика"""
    is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
    if is_guild_member:
        if admin and super_admin:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("🙋🏻‍♂️ Удалить игрока из базы данных", callback_data='del_player_db'))
            keyboard.add(types.InlineKeyboardButton("🗓 Проверка всех чатов на доступность", callback_data='check'))
            await call.message.answer("Служба по игрокам", reply_markup=keyboard)
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


def register_handlers_developer(dp: Dispatcher):
    dp.register_callback_query_handler(developer_commands, text='developer')
