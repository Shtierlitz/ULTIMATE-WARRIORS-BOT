# handlers/developer.py

from aiogram import types, Dispatcher

from src.decorators import member_super_admin_check


@member_super_admin_check
async def developer_commands(call: types.CallbackQuery):
    """Выводит инфо о командах разработчика"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🙋🏻‍♂️ Удалить игрока из базы данных", callback_data='del_player_db'))
    keyboard.add(types.InlineKeyboardButton("🗓 Проверка всех чатов на доступность", callback_data='check'))
    await call.message.answer("Служба по игрокам", reply_markup=keyboard)


def register_handlers_developer(dp: Dispatcher):
    dp.register_callback_query_handler(developer_commands, text='developer')
