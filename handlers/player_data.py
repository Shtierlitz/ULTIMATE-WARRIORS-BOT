# handlers/player_data.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from api_utils import PlayerData, GuildData
from create_bot import session, bot
from keyboards.players_kb import create_keyboard, create_player_info_keyboard
from sqlalchemy import func
from datetime import date
from db_models import Player


class PlayerState(StatesGroup):
    initial_state = State()
    player_name = State()
    player_data = State()
    back = State()


async def cancel_handler(message: types.Message, state: FSMContext):
    if message.text == 'cencel':
        await state.reset_state()
        await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())


async def player_buttons(message: types.Message, state: FSMContext):
    try:
        kb = create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
        await PlayerState.player_name.set()
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def player_info_buttons(message: types.Message, state: FSMContext):
    if message.text == 'cencel':
        return await cancel_handler(message, state)
    player_name = message.text[1:]  # Удалить символ '/' перед именем игрока
    if player_name == 'back':
        await back_handler(message, state)
    else:
        await state.update_data(player_name=player_name)

        today = date.today()  # текущая дата
        player = session.query(Player).filter(func.date(Player.update_time) == today,
                                              Player.name == player_name).first()
        if not player:  # Если игрока с таким именем нет в базе данных
            await state.reset_state()
            await message.answer('Игрок не найден. Выбор игрока отменён.', reply_markup=types.ReplyKeyboardRemove())
        else:
            kb = create_player_info_keyboard(player_name)  # Создать клавиатуру
            await message.reply(f"Выберете информацию об игроке {player_name}.", reply_markup=kb)
            await PlayerState.player_data.set()  # Изменить состояние


async def player_data_info(message: types.Message, state: FSMContext):
    """Возвращает выбранные данные по игроку"""
    if message.text == 'cencel':
        return await cancel_handler(message, state)
    data = await state.get_data()
    player_name = data.get("player_name")
    today = date.today()  # текущая дата
    player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
    if not player:  # Если игрока с таким именем нет в базе данных
        return  # Игнорировать сообщение

    key = message.text
    if key == 'back':
        await back_handler(message, state)
    elif key == 'all_data':
        player = session.query(Player).filter_by(name=player_name).first()
        player_str_list = PlayerData().extract_data(player)
        await bot.send_message(message.chat.id, player_str_list)
    elif key in player.__dict__:  # Проверяем, является ли ввод ключом в словаре атрибутов игрока
        player_data = player.__dict__[key]
        await message.reply(f"Данные {key} о пользователе {player.name}:\n{player_data}")
    else:  # Если ввод не является командой и не соответствует атрибутам игрока
        await state.reset_state()
        await message.answer('Неизвестная команда. Выбор данных игрока отменён.',
                             reply_markup=types.ReplyKeyboardRemove())


async def default_state_handler(message: types.Message, state: FSMContext):
    """Обработчик для всех неожиданных сообщений во время выбора данных игрока."""

    valid_commands = [column.name for column in Player.__table__.columns]
    valid_commands.append('cencel')
    valid_commands.append('all_data')

    if message.text not in valid_commands:
        await state.reset_state()
        await message.reply("Ввод не распознан. Выбор данных игрока отменён.",
                            reply_markup=types.ReplyKeyboardRemove())


async def back_handler(message: types.Message, state: FSMContext):
    """Обработчик для команды возврата к предыдущему выбору."""
    current_state = await state.get_state()
    if current_state == "PlayerState:player_data":
        kb = create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
        await PlayerState.player_name.set()
    elif current_state == "PlayerState:player_name":
        await PlayerState.initial_state.set()
        await message.answer('Вернулись к началу', reply_markup=types.ReplyKeyboardRemove())
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
