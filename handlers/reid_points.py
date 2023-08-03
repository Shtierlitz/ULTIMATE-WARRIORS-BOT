# handlers/reid_points_state.py

from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery

from src.decorators import member_check_call
from src.player import PlayerScoreService


@member_check_call
async def start_cmd_handler(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✴️ Энка за сегодня", callback_data='raid_points'))
    keyboard.add(types.InlineKeyboardButton("⌛️ Энка за месяц", callback_data='raid_points_all'))
    keyboard.add(types.InlineKeyboardButton("💪🏻 Топ 10 за неделю", callback_data='raid_top_week'))
    keyboard.add(types.InlineKeyboardButton("🦾 Чемпионы месяца", callback_data='raid_top_month'))
    keyboard.add(types.InlineKeyboardButton("🪫 Лентяи сегодня", callback_data='raid_lazy'))
    keyboard.add(types.InlineKeyboardButton("🔪 Лентяи вчера 🔪", callback_data='raid_yesterday'))
    keyboard.add(types.InlineKeyboardButton("⚰️ Дно недели ⚰️", callback_data='raid_lazy_week'))
    keyboard.add(types.InlineKeyboardButton("☠️ Кандидаты на вылет за месяц ☠️", callback_data='raid_lazy_month'))
    await call.message.answer("🔋Энка сервис🔋", reply_markup=keyboard)



@member_check_call
async def raid_points_handler(call: CallbackQuery):
    """Показывает энку за сегодняшний день"""
    message_strings = await PlayerScoreService.get_raid_scores()
    await call.message.answer(message_strings)


@member_check_call
async def raid_points_all_handler(call: CallbackQuery):
    """Показывает энку за месяц"""
    message_strings = await PlayerScoreService.get_raid_scores_all()
    await call.message.answer(message_strings)


@member_check_call
async def raid_lazy_handler(call: CallbackQuery):
    """Показывает кто за сегодня не досдал энку"""
    message_strings = await PlayerScoreService.get_reid_lazy_fools()
    await call.message.answer(message_strings)


@member_check_call
async def raid_lazy_yesterday_handler(call: CallbackQuery):
    """Показывает кто недосдал за вчера"""
    message_strings = await PlayerScoreService.get_reid_lazy_fools('yesterday')
    await call.message.answer(message_strings)


@member_check_call
async def raid_lazy_week_handler(call: CallbackQuery):
    """Показывает кто всех лентяев недели"""
    message_strings = await PlayerScoreService.get_least_reid_lazy_fools('week')
    await call.message.answer(message_strings)


@member_check_call
async def raid_lazy_month_handler(call: CallbackQuery):
    """Показывает всех лентяев месяца"""
    message_strings = await PlayerScoreService.get_least_reid_lazy_fools('month')
    await call.message.answer(message_strings)


@member_check_call
async def raid_top_week_handler(call: CallbackQuery):
    """Показывает чемпионов недели по энке"""
    message_strings = await PlayerScoreService.get_least_reid_lazy_fools('week', least=False)
    await call.message.answer(message_strings)


@member_check_call
async def raid_top_month_handler(call: CallbackQuery):
    """Чемпионы месяца по энке"""
    message_strings = await PlayerScoreService.get_least_reid_lazy_fools('month', least=False)
    await call.message.answer(message_strings)


def register_handlers_reid(dp: Dispatcher):
    dp.register_callback_query_handler(start_cmd_handler, text='reid')
    dp.register_callback_query_handler(raid_points_handler, text='raid_points', state='*')
    dp.register_callback_query_handler(raid_points_all_handler, text='raid_points_all', state='*')
    dp.register_callback_query_handler(raid_lazy_handler, text='raid_lazy', state='*')
    dp.register_callback_query_handler(raid_lazy_week_handler, text='raid_lazy_week', state='*')
    dp.register_callback_query_handler(raid_lazy_month_handler, text='raid_lazy_month', state='*')
    dp.register_callback_query_handler(raid_lazy_yesterday_handler, text='raid_yesterday', state='*')
    dp.register_callback_query_handler(raid_top_week_handler, text='raid_top_week', state='*')
    dp.register_callback_query_handler(raid_top_month_handler, text='raid_top_month', state='*')
