# handlers/player_data.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from middlewares.user_check import guild_members
from src.graphics import get_player_gp_graphic, get_player_rank_graphic
from src.player import PlayerData
from src.guild import GuildData
from create_bot import bot
from settings import async_session_maker
from keyboards.players_kb import create_keyboard, create_player_info_keyboard
from sqlalchemy import func, select
from datetime import date
from db_models import Player
from src.utils import get_new_day_start, get_player_by_name_or_nic


class PlayerState(StatesGroup):
    initial_state = State()
    player_name = State()
    player_data = State()
    back = State()


async def cancel_handler(message: types.Message, state: FSMContext):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        if message.text == 'cencel':
            await state.reset_state()
            await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())


async def player_buttons(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    is_guild_member = any(
        user_id in member.values() for dictionary in guild_members for member in dictionary.values())
    if is_guild_member:
        kb = await create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
        await PlayerState.player_name.set()


async def player_info_buttons(message: types.Message, state: FSMContext):
    """Открывает панель кнопок с инфой об игроке"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        if message.text == 'cencel':
            return await cancel_handler(message, state)
        player_name = message.text
        if player_name == 'back':
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
            await message.answer('Игрок не найден. Выбор игрока отменён.', reply_markup=types.ReplyKeyboardRemove())
        else:
            kb = await create_player_info_keyboard(player_name)  # Создать клавиатуру
            await message.reply(f"Выберете информацию об игроке {player_name}.", reply_markup=kb)
            await PlayerState.player_data.set()  # Изменить состояние


async def player_data_info(message: types.Message, state: FSMContext):
    """Возвращает выбранные данные по игроку"""
    is_guild_member = message.conf.get('is_guild_member', False)
    if not is_guild_member or message.text == 'cancel':
        return await cancel_handler(message, state)

    data = await state.get_data()
    player_name = data.get("player_name")
    player = await get_player_by_name_or_nic(player_name)

    if not player:  # Если игрока с таким именем нет в базе данных
        return await cancel_handler(message, state)

    key = message.text
    if key == 'back':
        return await back_handler(message, state)

    graphic_keys = {
        "GP_month": (get_player_gp_graphic, (player.name, 'month')),
        "GP_year": (get_player_gp_graphic, (player.name, 'year')),
        "arena_graphic_month": (get_player_rank_graphic, (player.name, 'month', False)),
        "fleet_arena_graphic_month": (get_player_rank_graphic, (player.name, 'month', True)),
        "arena_graphic_year": (get_player_rank_graphic, (player.name, 'year', False)),
        "fleet_arena_graphic_year": (get_player_rank_graphic, (player.name, 'year', True)),
    }

    if key in graphic_keys:
        try:
            func, args = graphic_keys[key]
            image = await func(*args)
            return await bot.send_photo(chat_id=message.chat.id, photo=image)
        except Exception as e:
            return await message.reply(f"Произошла ошибка при построении графика: \n\n❌❌{e}❌❌\n\n"
                                       f"Возможно у вас просто первый день и данных езе нет в базе за 2-3 дня хотябы.\n"
                                       f"Если это так, то просто подождите пару дней.")
    if key == 'all_data':
        all_data = await PlayerData().extract_data(player)
        return await message.reply(all_data)

    if key in player.__dict__:
        player_data = player.__dict__[key]
        return await message.reply(f"Данные {key} о пользователе {player.name}:\n{player_data}")

    # Если ввод не является командой и не соответствует атрибутам игрока
    await state.reset_state()
    return await message.answer('Неизвестная команда. Выбор данных игрока отменён.',
                                reply_markup=types.ReplyKeyboardRemove())


async def default_state_handler(message: types.Message, state: FSMContext):
    """Обработчик для всех неожиданных сообщений во время выбора данных игрока."""
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:

        valid_commands = [column.name for column in Player.__table__.columns]
        valid_commands.append('cencel')
        valid_commands.append('all_data')

        if message.text not in valid_commands:
            await state.reset_state()
            await message.reply("Ввод не распознан. Выбор данных игрока отменён.",
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
            await player_buttons(message, state)
        else:
            await state.finish()


def register_handlers_player(dp: Dispatcher):
    dp.register_message_handler(player_buttons, commands=['player'])

    dp.register_message_handler(cancel_handler, commands=['cencel'], state="*")  # Обработчик команды отмены

    dp.register_message_handler(player_info_buttons, content_types=types.ContentType.TEXT,
                                state=PlayerState.player_name)
    dp.register_message_handler(player_data_info, content_types=types.ContentType.TEXT, state=PlayerState.player_data)
    dp.register_message_handler(back_handler, commands=['back'], state="*")  # Обработчик команды возврата

    dp.register_message_handler(default_state_handler, content_types=types.ContentType.TEXT,
                                state=[PlayerState.player_name, PlayerState.player_data])
