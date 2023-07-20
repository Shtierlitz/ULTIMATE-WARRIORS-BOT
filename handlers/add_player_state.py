# handlers/add_player_state.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import add_player_to_ids


class AddPlayer(StatesGroup):
    ally_code = State()
    player_name = State()
    tg_nic = State()
    tg_id = State()


def get_keyboard():
    """Создает клавиатуру с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
    keyboard.add(cancel_button)
    return keyboard


async def start_add_player(message: types.Message):
    """Начинает сиквенцию"""
    keyboard = get_keyboard()
    await message.answer("Начинаем сиквенцию добавления персонажа в ids.json\nВведите код союзника.",
                         reply_markup=keyboard)
    await AddPlayer.ally_code.set()


async def process_ally_code(message: types.Message, state: FSMContext):
    """Добавляет код союзника и просит ввести имя игрока"""
    async with state.proxy() as data:
        keyboard = get_keyboard()
        data['ally_code'] = message.text
        await message.answer("Теперь введите имя игрока в игре.",
                             reply_markup=keyboard)
    await AddPlayer.next()


async def process_player_name(message: types.Message, state: FSMContext):
    """Добавляет имя игрока и просит ввести ник телеги"""
    async with state.proxy() as data:
        keyboard = get_keyboard()
        data['player_name'] = message.text
        await message.answer("Теперь введите имя телеграм ник.",
                             reply_markup=keyboard)
    await AddPlayer.next()


async def process_tg_nic(message: types.Message, state: FSMContext):
    """Вводит телеграм ник и просит ввести тг ID"""
    async with state.proxy() as data:
        keyboard = get_keyboard()
        data['tg_nic'] = message.text
        await message.answer("Теперь введите ТГ ID.",
                             reply_markup=keyboard)
    await AddPlayer.next()


async def process_tg_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['tg_id'] = message.text
    data = await state.get_data()

    await add_player_to_ids(message, data)

    await state.finish()


async def cancel_add_player(call: types.CallbackQuery, state: FSMContext):
    """Завершает сиквенцию добавления персонажа"""
    await state.finish()
    await call.message.answer("Добавление персонажа отменено.")


def register_handlers_add_player(dp: Dispatcher):
    dp.register_message_handler(start_add_player, commands='add_player', is_chat_admin=True)
    dp.register_message_handler(process_ally_code, state=AddPlayer.ally_code, is_chat_admin=True)
    dp.register_message_handler(process_player_name, state=AddPlayer.player_name, is_chat_admin=True)
    dp.register_message_handler(process_tg_nic, state=AddPlayer.tg_nic, is_chat_admin=True)
    dp.register_message_handler(process_tg_id, state=AddPlayer.tg_id, is_chat_admin=True)
    dp.register_callback_query_handler(cancel_add_player, text="cancel",
                                       state=AddPlayer.all_states)  # Обработчик кнопки отмены
