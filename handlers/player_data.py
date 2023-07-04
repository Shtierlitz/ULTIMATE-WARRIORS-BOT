# handlers/player_data.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from api_utils import get_player_filtered_data, extract_data
from create_bot import session, bot
from keyboards.players_kb import create_keyboard, create_player_info_keyboard
from sqlalchemy import func
from datetime import date
from db_models import Player


class PlayerState(StatesGroup):
    player_name = State()
    player_data = State()


async def player_buttons(message: types.Message, state: FSMContext):
    try:
        kb = create_keyboard()  # Создать клавиатуру
        await message.reply("Выберете члена гильдии.", reply_markup=kb)  # Отправить сообщение с клавиатурой
        await PlayerState.player_name.set()
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")



async def player_info_buttons(message: types.Message, state: FSMContext):
    player_name = message.text[1:]  # Удалить символ '/' перед именем игрока
    if player_name == 'encel':
        await state.reset_state()
        await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())
    else:
        await state.update_data(player_name=player_name)

        today = date.today()  # текущая дата
        player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
        if not player:  # Если игрока с таким именем нет в базе данных
            return  # Игнорировать сообщение
        kb = create_player_info_keyboard(player_name)  # Создать клавиатуру
        await message.reply(f"Выберете информацию об игроке {player_name}.", reply_markup=kb)
        await PlayerState.player_data.set()  # Изменить состояние


async def player_data_info(message: types.Message, state: FSMContext):
    """Возвращает выбранные данные по игроку"""
    data = await state.get_data()
    player_name = data.get("player_name")
    today = date.today()  # текущая дата
    player = session.query(Player).filter(func.date(Player.update_time) == today, Player.name == player_name).first()
    if not player:  # Если игрока с таким именем нет в базе данных
        return  # Игнорировать сообщение
    key = message.text
    if key == 'cencel':
        await state.reset_state()
        await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())
    elif key == 'all_data':
        player = session.query(Player).filter_by(name=player_name).first()
        player_str_list = extract_data(player)
        await bot.send_message(message.chat.id, player_str_list)
    else:
        player_data = player.__dict__[key]
        await message.reply(f"Данные {key} о пользователе {player.name}:\n{player_data}")

async def default_state_handler(message: types.Message, state: FSMContext):
    """Обработчик для всех неожиданных сообщений во время выбора данных игрока."""

    valid_commands = [column.name for column in Player.__table__.columns]
    valid_commands.append('cencel')
    valid_commands.append('all_data')

    if message.text not in valid_commands:
        await state.reset_state()
        await message.reply("Ввод не распознан. Выбор данных игрока отменён.",
                            reply_markup=types.ReplyKeyboardRemove())


def register_handlers_player(dp: Dispatcher):
    dp.register_message_handler(player_buttons, commands=['player'])
    dp.register_message_handler(player_info_buttons, content_types=types.ContentType.TEXT, state=PlayerState.player_name)
    dp.register_message_handler(player_data_info, content_types=types.ContentType.TEXT, state=PlayerState.player_data)
    dp.register_message_handler(default_state_handler, content_types=types.ContentType.TEXT, state=[PlayerState.player_name, PlayerState.player_data])


