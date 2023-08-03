# delete_player_db_state.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import bot
from handlers.add_player_state import get_keyboard, cancel_state
from src.decorators import member_super_admin_check, member_admin_super_state_message_check
from src.utils import delete_db_player_data, is_member_admin_super


class DeletePlayerDB(StatesGroup):
    waiting_for_player_name = State()


@member_super_admin_check
async def start_del_player(call: types.CallbackQuery):
    """Запрошивает имя или код союзника для удаления из БД"""
    keyboard = get_keyboard()
    await call.message.reply("Пожалуйста, предоставьте имя игрока в игре или код союзника.", reply_markup=keyboard)
    await DeletePlayerDB.waiting_for_player_name.set()


@member_admin_super_state_message_check
async def del_player(message: types.Message, state: FSMContext):
    """Удаляет из бд"""
    player_name = message.text
    mes = await delete_db_player_data(player_name)
    if mes:
        await bot.send_message(message.chat.id,
                               f"Записи игрока {mes} безвозвратно удалены из базы данных ⚰️\n"
                               f"Поделом засранцу! 👹")
        # Finish the conversation
        await state.finish()
    else:
        await state.finish()


def register_handlers_delete_db_player(dp: Dispatcher):
    dp.register_callback_query_handler(start_del_player, text='del_player_db', state='*')
    dp.register_message_handler(del_player, state=DeletePlayerDB.waiting_for_player_name)
    dp.register_callback_query_handler(cancel_state, text="cancel",
                                       state=DeletePlayerDB.all_states)  # Обработчик кнопки отмены
