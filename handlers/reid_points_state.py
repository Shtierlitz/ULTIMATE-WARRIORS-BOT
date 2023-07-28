# handlers/reid_points_state.py

from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery

from src.player import PlayerScoreService


async def start_cmd_handler(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("✴️Энка за сегодня", callback_data='raid_points'))
        keyboard.add(types.InlineKeyboardButton("⌛️Энка за месяц", callback_data='raid_points_all'))
        keyboard.add(types.InlineKeyboardButton("🪫Лентяи сегодня", callback_data='raid_lazy'))
        keyboard.add(types.InlineKeyboardButton("🔪Лентяи вчера", callback_data='raid_yesterday'))
        await message.answer("🔋Энка сервис🔋", reply_markup=keyboard)


async def raid_points_handler(call: CallbackQuery):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        message_strings = await PlayerScoreService.get_raid_scores()
        await call.message.answer(message_strings)
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def raid_points_all_handler(call: CallbackQuery):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        message_strings = await PlayerScoreService.get_raid_scores_all()
        await call.message.answer(message_strings)
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def raid_lazy_handler(call: CallbackQuery):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        message_strings = await PlayerScoreService.get_reid_lazy_fools()
        await call.message.answer(message_strings)
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def raid_lazy_yesterday_handler(call: CallbackQuery):
    is_guild_member = call.message.conf.get('is_guild_member', False)
    if is_guild_member:
        message_strings = await PlayerScoreService.get_reid_lazy_fools(yesterday=True)
        await call.message.answer(message_strings)
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


def register_handlers_reid(dp: Dispatcher):
    dp.register_message_handler(start_cmd_handler, commands='reid')
    dp.register_callback_query_handler(raid_points_handler, text='raid_points', state='*')
    dp.register_callback_query_handler(raid_points_all_handler, text='raid_points_all', state='*')
    dp.register_callback_query_handler(raid_lazy_handler, text='raid_lazy', state='*')
    dp.register_callback_query_handler(raid_lazy_yesterday_handler, text='raid_yesterday', state='*')
