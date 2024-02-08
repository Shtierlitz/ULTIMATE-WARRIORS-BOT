# get_unit_state.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from create_bot import bot
from handlers.add_player_state import get_keyboard, cancel_state
from src.decorators import member_check_call, member_admin_state_message_check, member_state_message_check
from src.player_units_provider import PlayerUnitsProvider


class GetUnit(StatesGroup):
    waiting_for_unit_name = State()


@member_check_call
async def start_find_unit(call: types.CallbackQuery):
    """Запрашивает символы из имени юнита"""
    keyboard = get_keyboard()
    await call.message.reply(
        "Пожалуйста, предоставьте имя пользователя у которого вы хотите получить юниты.",
        reply_markup=keyboard
    )
    await GetUnit.waiting_for_unit_name.set()


@member_state_message_check
async def find_unit(message: types.Message, state: FSMContext):
    """Достает данные юнита из базы"""
    player_name = message.text
    units = await PlayerUnitsProvider().get_units(message, player_name)
    if not units:
        await bot.send_message(
            message.chat.id,
            f"❌ Юнитов с такими буквами в имени не найдено./n"
            f"Не обновлена база либо юнит у игрока не открыт."
        )
        await state.finish()

    await bot.send_message(message.chat.id, units)
    # Finish the conversation
    await state.finish()


def register_handlers_find_unit(dp: Dispatcher):
    dp.register_callback_query_handler(start_find_unit, text='find_unit', state='*')
    dp.register_message_handler(find_unit, state=GetUnit.waiting_for_unit_name)
    dp.register_callback_query_handler(cancel_state, text="cancel",
                                       state=GetUnit.all_states)
