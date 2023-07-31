# handlers/add_player_state.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import add_player_to_ids, is_member_admin_super


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


async def start_add_player(call: types.CallbackQuery, state: FSMContext):
    """Начинает секвенцию"""
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            keyboard = get_keyboard()
            await call.message.answer("Начинаем секвенцию добавления персонажа в ids.json\n"
                                      "Введите код союзника без черточек.",
                                      reply_markup=keyboard)
            await AddPlayer.ally_code.set()
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def process_ally_code(message: types.Message, state: FSMContext):
    """Добавляет код союзника и просит ввести имя игрока"""
    is_guild_member, admin = await is_member_admin_super(message=message)
    if is_guild_member:
        if admin:
            async with state.proxy() as data:
                keyboard = get_keyboard()
                data['ally_code'] = message.text
                await message.answer("Теперь введите имя игрока в игре.",
                                     reply_markup=keyboard)
            await AddPlayer.next()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def process_player_name(message: types.Message, state: FSMContext):
    """Добавляет имя игрока и просит ввести ник телеги"""
    is_guild_member, admin = await is_member_admin_super(message=message)
    if is_guild_member:
        if admin:
            async with state.proxy() as data:
                keyboard = get_keyboard()
                data['player_name'] = message.text
                await message.answer("Теперь введите имя телеграм ник. (Без @)",
                                     reply_markup=keyboard)
            await AddPlayer.next()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def process_tg_nic(message: types.Message, state: FSMContext):
    """Вводит телеграм ник и просит ввести тг ID"""
    is_guild_member, admin = await is_member_admin_super(message=message)
    if is_guild_member:
        if admin:
            async with state.proxy() as data:
                keyboard = get_keyboard()
                data['tg_nic'] = message.text
                await message.answer("Теперь введите ТГ ID.\nТот длинный код из бота - @getmyid_bot",
                                     reply_markup=keyboard)
            await AddPlayer.next()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def process_tg_id(message: types.Message, state: FSMContext):
    is_guild_member, admin = await is_member_admin_super(message=message)
    if is_guild_member:
        if admin:
            async with state.proxy() as data:
                data['tg_id'] = message.text
            data = await state.get_data()

            await add_player_to_ids(message, data)

            await state.finish()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def cancel_state(call: types.CallbackQuery, state: FSMContext):
    """Завершает секвенцию"""
    await state.finish()
    await call.message.answer("Добавление персонажа отменено.")


def register_handlers_add_player(dp: Dispatcher):
    dp.register_callback_query_handler(start_add_player, text='add_player', state='*', is_chat_admin=True)
    dp.register_message_handler(process_ally_code, state=AddPlayer.ally_code)
    dp.register_message_handler(process_player_name, state=AddPlayer.player_name)
    dp.register_message_handler(process_tg_nic, state=AddPlayer.tg_nic)
    dp.register_message_handler(process_tg_id, state=AddPlayer.tg_id)
    dp.register_callback_query_handler(cancel_state, text="cancel",
                                       state=AddPlayer.all_states)  # Обработчик кнопки отмены
