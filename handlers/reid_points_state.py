from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery

from src.player import PlayerScoreService


class RaidState(StatesGroup):
    RaidPoints = State()  # состояние, когда пользователь выбирает "Сегодня"
    RaidPointsAll = State()  # состояние, когда пользователь выбирает "Месяц"
    RaidLazy = State()  # состояние, когда пользователь выбирает "Летняи"
    RaidLazyYeserday = State()  # Вчера


# @dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✴️Энка за сегодня", callback_data='raid_points'))
    keyboard.add(types.InlineKeyboardButton("⌛️Энка за месяц", callback_data='raid_points_all'))
    keyboard.add(types.InlineKeyboardButton("🪫Лентяи сегодня", callback_data='raid_lazy'))
    keyboard.add(types.InlineKeyboardButton("🔪Лентяи вчера", callback_data='raid_yesterday'))
    await message.answer("🔋Энка сервис🔋", reply_markup=keyboard)


async def raid_points_handler(call: CallbackQuery, state: FSMContext):
    await RaidState.RaidPoints.set()
    message_strings = await PlayerScoreService.get_raid_scores()
    await call.message.answer(message_strings)


async def raid_points_all_handler(call: CallbackQuery, state: FSMContext):
    await RaidState.RaidPointsAll.set()
    message_strings = await PlayerScoreService.get_raid_scores_all()
    await call.message.answer(message_strings)


async def raid_lazy_handler(call: CallbackQuery, state: FSMContext):
    await RaidState.RaidLazy.set()
    message_strings = await PlayerScoreService.get_reid_lazy_fools()
    await call.message.answer(message_strings)


async def raid_lazy_yesterday_handler(call: CallbackQuery, state: FSMContext):
    await RaidState.RaidLazy.set()
    message_strings = await PlayerScoreService.get_reid_lazy_fools(yesterday=True)
    await call.message.answer(message_strings)


def register_handlers_reid(dp: Dispatcher):
    dp.register_message_handler(start_cmd_handler, commands='reid')
    dp.register_callback_query_handler(raid_points_handler, text='raid_points', state='*')
    dp.register_callback_query_handler(raid_points_all_handler, text='raid_points_all', state='*')
    dp.register_callback_query_handler(raid_lazy_handler, text='raid_lazy', state='*')
    dp.register_callback_query_handler(raid_lazy_yesterday_handler, text='raid_yesterday', state='*')
