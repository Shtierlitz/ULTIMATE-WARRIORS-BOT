# get_unit_state.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from create_bot import bot
from handlers.add_player_state import get_keyboard, cancel_state
from src.decorators import member_check_call, member_admin_state_message_check, member_state_message_check
from src.player import PlayerData
from src.player_units_provider import PlayerUnitsProvider, PlayerUnitDataService


class GetUnit(StatesGroup):
    waiting_for_player_name = State()
    waiting_for_unit_name = State()


@member_check_call
async def start_find_unit(call: types.CallbackQuery):
    """Запрашивает символы из имени юнита"""
    keyboard = get_keyboard()
    await call.message.reply(
        "Пожалуйста, предоставьте имя пользователя у которого вы хотите получить юниты.",
        reply_markup=keyboard
    )
    await GetUnit.waiting_for_player_name.set()


@member_state_message_check
async def find_player(message: types.Message, state: FSMContext):
    """Достает данные юнита из базы"""
    keyboard = get_keyboard()
    player_name = message.text
    if player_name == 'Отмена':
        await state.finish()
        await message.answer("❌ Действие отменено", reply_markup=keyboard)
        return
    player = await PlayerData().get_player(player_name)
    if not player:
        await bot.send_message(
            message.chat.id,
            f'❌ Игрок с именем {player_name} отсутствует\n'
            'Проверьте правильность написания имени',
            reply_markup=keyboard
        )
        await GetUnit.waiting_for_player_name.set()
        return
    # Сохраняем имя игрока во временном хранилище состояния
    await state.update_data(player=player)
    await message.answer(
        'Пожалуйста, введите имя юнита.',
        reply_markup=keyboard
    )
    # Переходим к состоянию ожидания имени юнита
    await GetUnit.waiting_for_unit_name.set()


@member_state_message_check
async def find_unit_character(message: types.Message, state: FSMContext):
    """Ищет и отправляет информацию о юните"""
    unit_name = message.text
    keyboard = get_keyboard()
    if unit_name == 'Отмена':
        await state.finish()
        await message.answer("❌ Действие отменено")
        return
    user_data = await state.get_data()
    player = user_data['player']
    units = await PlayerUnitDataService().get_unit_data_by_name(player, unit_name)
    if not units:
        await bot.send_message(
            message.chat.id,
            f'❌ Юнитов с такими буквами в имени не найдено.\n'
            f'Проверьте правильность написания имени юнита.\n'
            f'Если все верно, то не обновлена база либо юнит у игрока не открыт.',
            reply_markup=keyboard
        )
        await GetUnit.waiting_for_unit_name.set()
        return
    units = await PlayerUnitsProvider().convert_unit_data_to_message(units)
    await bot.send_message(message.chat.id, units, reply_markup=keyboard)
    # Finish the conversation
    await GetUnit.waiting_for_unit_name.set()


def register_handlers_find_unit(dp: Dispatcher):
    dp.register_callback_query_handler(start_find_unit, text='find_unit', state='*')
    dp.register_message_handler(find_player, state=GetUnit.waiting_for_player_name)
    dp.register_message_handler(find_unit_character, state=GetUnit.waiting_for_unit_name)
    dp.register_callback_query_handler(cancel_state, text="cancel",
                                       state=GetUnit.all_states)
