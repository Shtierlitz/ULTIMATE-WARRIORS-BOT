# handlers/player_data.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from middlewares.user_check import guild_members
from src.graphics import get_player_gp_graphic, get_player_rank_graphic, get_month_player_graphic
from src.player import PlayerData
from create_bot import bot
from keyboards.players_kb import create_keyboard, create_player_info_keyboard
from db_models import Player
from src.utils import get_player_by_name_or_nic
from typing import Union, Optional


class PlayerState(StatesGroup):
    initial_state = State()
    player_name = State()
    player_data = State()
    back = State()


async def cancel_handler(message: types.Message, state: FSMContext):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        if message.text == 'Отмена❌':
            await state.reset_state()
            await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())


async def player_buttons(call: Union[types.CallbackQuery, types.Message], state: Optional[FSMContext] = None):
    if isinstance(call, types.CallbackQuery):
        user_id = str(call.from_user.id)
        message = call.message
    elif isinstance(call, types.Message):
        user_id = str(call.from_user.id)
        message = call
    else:
        raise ValueError("call должен быть типа CallbackQuery или Message")

    is_guild_member = any(
        user_id in member.values() for dictionary in guild_members for member in dictionary.values())
    if is_guild_member:
        kb = await create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
        if state:
            await PlayerState.player_name.set()


async def player_info_buttons(message: types.Message, state: FSMContext):
    """Открывает панель кнопок с инфой об игроке"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        if message.text == 'Отмена❌':
            return await cancel_handler(message, state)
        player_name = message.text
        if player_name == '🔙Назад':
            await back_handler(message, state)
        if player_name.startswith("@"):
            player_name = player_name.replace("@", "")
            await state.update_data(player_name=player_name)
            player = await get_player_by_name_or_nic(player_name)
        else:
            await state.update_data(player_name=player_name)
            player = await get_player_by_name_or_nic(player_name)

        if not player:  # Если игрока с таким именем нет в базе данных
            await state.reset_state()
            await message.answer('❌ Игрок не найден. Выбор игрока отменён.', reply_markup=types.ReplyKeyboardRemove())
        else:
            kb = await create_player_info_keyboard(player_name)  # Создать клавиатуру
            await message.reply(f"Выберете информацию об игроке {player_name}.", reply_markup=kb)
            await PlayerState.player_data.set()  # Изменить состояние


async def player_data_info(message: types.Message, state: FSMContext):
    """Возвращает выбранные данные по игроку"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if not is_guild_member or message.text == 'Отмена❌':
        return await cancel_handler(message, state)

    data = await state.get_data()
    player_name = data.get("player_name")
    player = await get_player_by_name_or_nic(player_name)

    if not player:  # Если игрока с таким именем нет в базе данных
        return await cancel_handler(message, state)

    key = message.text
    if key == '🔙Назад':
        return await back_handler(message, state)

    graphic_keys = {
        "📊 ГМ за месяц": (get_player_gp_graphic, (player.name, 'month')),
        "📊 ГМ за все время": (get_player_gp_graphic, (player.name, 'year')),
        "📊 пешка за месяц": (get_player_rank_graphic, (player.name, 'month', False)),
        "📊 флот за месяц": (get_player_rank_graphic, (player.name, 'month', True)),
        "📊 пешка за все время": (get_player_rank_graphic, (player.name, 'year', False)),
        "📊 флот за все время": (get_player_rank_graphic, (player.name, 'year', True)),
        "📊 энка за месяц": (get_month_player_graphic, (player.name,))  # передаем имя игрока напрямую, а не в кортеже
    }

    if key in graphic_keys:
        try:
            func, args = graphic_keys[key]
            image = await func(*args)
            return await bot.send_photo(chat_id=message.chat.id, photo=image)
        except Exception as e:
            return await message.reply(f"Произошла ошибка при построении графика: \n\n❌❌{e}❌❌\n\n"
                                       f"Возможно у вас просто первый день и данных езе нет в базе за 2-3 дня хотя бы.\n"
                                       f"Если это так, то просто подождите пару дней.")
    if key == '🗒Все данные':
        all_data = await PlayerData().extract_data(player)
        return await message.reply(all_data)

    # Если ввод не является командой и не соответствует атрибутам игрока
    await state.reset_state()
    return await message.answer('❌ Неизвестная команда. Выбор данных игрока отменён.',
                                reply_markup=types.ReplyKeyboardRemove())


async def default_state_handler(message: types.Message, state: FSMContext):
    """Обработчик для всех неожиданных сообщений во время выбора данных игрока."""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:

        valid_commands = [column.name for column in Player.__table__.columns]
        valid_commands.append('🔙Назад')
        valid_commands.append('Все данные')

        if message.text not in valid_commands:
            await state.reset_state()
            await message.reply("❌ Ввод не распознан. Выбор данных игрока отменён.",
                                reply_markup=types.ReplyKeyboardRemove())


async def back_handler(message: types.Message, state: FSMContext):
    """Обработчик для команды возврата к предыдущему выбору."""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        current_state = await state.get_state()
        if current_state == "PlayerState:player_data":
            kb = await create_keyboard()  # Создать клавиатуру
            await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
            await PlayerState.player_name.set()
        elif current_state == "PlayerState:player_name":
            await PlayerState.initial_state.set()
            await message.answer('Вернулись к началу', reply_markup=types.ReplyKeyboardRemove())
            # Добавьте вызов функции, которая обрабатывает начальное состояние
            await player_buttons(message)
        else:
            await state.finish()


def register_handlers_player(dp: Dispatcher):
    dp.register_callback_query_handler(player_buttons, text='player')

    dp.register_message_handler(cancel_handler, commands=['cencel'], state="*")  # Обработчик команды отмены

    dp.register_message_handler(player_info_buttons, content_types=types.ContentType.TEXT,
                                state=PlayerState.player_name)
    dp.register_message_handler(player_data_info, content_types=types.ContentType.TEXT, state=PlayerState.player_data)
    dp.register_message_handler(back_handler, commands=['back'], state="*")  # Обработчик команды возврата

    dp.register_message_handler(default_state_handler, content_types=types.ContentType.TEXT,
                                state=[PlayerState.player_name, PlayerState.player_data])
