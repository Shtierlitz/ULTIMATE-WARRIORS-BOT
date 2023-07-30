# handlers/admin.py

from aiogram import types, Dispatcher

from create_bot import bot
import io
import os

from src.graphics import get_guild_galactic_power
from src.guild import GuildData
from src.player import PlayerData
from src.utils import get_players_list_from_ids, \
    check_guild_players, is_admin, is_member_admin_super


async def player_cmd_handler(call: types.CallbackQuery):
    is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
    if is_guild_member:
        if admin and super_admin:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Добавить игрока в бот", callback_data='add_player'))
            keyboard.add(types.InlineKeyboardButton("🗓 Список всех", callback_data='players_list'))
            keyboard.add(types.InlineKeyboardButton("🔪 Удалить игрока из бота", callback_data='delete_player'))
            await call.message.answer("👮🏻‍♂️ Служба по игрокам", reply_markup=keyboard)
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def admin_command_help(update: [types.Message, types.CallbackQuery]):
    if isinstance(update, types.Message):
        user_id = update.from_user.id
        chat_id = update.chat.id
        message_or_call = update
    elif isinstance(update, types.CallbackQuery):
        user_id = update.from_user.id
        chat_id = update.message.chat.id
        message_or_call = update.message
    else:
        # Неизвестный тип обновления, выходим из функции
        return

    is_guild_member = message_or_call.conf.get('is_guild_member', False)
    admin = await is_admin(bot, user_id, chat_id)
    if is_guild_member:
        if admin:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("✍🏻 Групповое сообщение", callback_data='group'))
            keyboard.add(types.InlineKeyboardButton("✉️ Сообщение всем", callback_data='group_all'))
            keyboard.add(types.InlineKeyboardButton("🙋🏻‍♂️ Запись/удаление игрока в бот", callback_data='players'))
            keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за месяц", callback_data='guild_month'))
            keyboard.add(types.InlineKeyboardButton("📊 График ГМ гильдии за год", callback_data='guild_year'))
            keyboard.add(types.InlineKeyboardButton("🏗 Экстреннее обновление БД", callback_data='refresh'))
            keyboard.add(
                types.InlineKeyboardButton("☠️ Команды разработчика ☠️", callback_data='developer'))
            await message_or_call.answer("👮🏻‍♂️ Админ панель 👮🏻", reply_markup=keyboard)
        else:
            await message_or_call.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await message_or_call.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def command_db_extra(call: types.CallbackQuery):
    """Стартуем бот и обновляем БД"""
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            try:
                await bot.send_message(call.message.chat.id,
                                       "ОБаза данных обновляется в фоне.\nМожно приступать к работе.")
                is_dev = os.environ.get('IS_DEV', default=False)
                print(is_dev)
                await GuildData().build_db()
                await PlayerData().update_players_data()
            except Exception as e:
                print(e)
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def players_list(call: types.CallbackQuery):
    """Отправляет содержимое файла ids.json в чат"""
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            try:
                final_msg_1, final_msg_2 = await get_players_list_from_ids(call.message)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_1)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), final_msg_2)

            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def send_month_guild_grafic(call: types.CallbackQuery):
    """Отправляет график мощи гильдии"""
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="month")
                await bot.send_photo(chat_id=call.message.chat.id, photo=image)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def send_year_guild_graphic(call: types.CallbackQuery):
    """Отправляет график рейда игрока"""
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            try:
                image: io.BytesIO = await get_guild_galactic_power(period="year")
                await bot.send_photo(chat_id=call.message.chat.id, photo=image)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
            "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


async def check_ids(call: types.CallbackQuery):
    is_guild_member, admin = await is_member_admin_super(call)
    if is_guild_member:
        if admin:
            try:
                await check_guild_players(call.message)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
    else:
        await call.message.answer(
            "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. "
            "Комманда запрещена.\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")


def register_handlers_admin(dp: Dispatcher):
    dp.register_callback_query_handler(command_db_extra, text='refresh')
    dp.register_callback_query_handler(players_list, text=['players_list'], state='*')
    dp.register_callback_query_handler(admin_command_help, text='admin')
    dp.register_message_handler(admin_command_help, commands='admin')
    dp.register_callback_query_handler(send_month_guild_grafic, text='guild_month')
    dp.register_callback_query_handler(send_year_guild_graphic, text='guild_year')
    dp.register_callback_query_handler(check_ids, text='check')
    dp.register_callback_query_handler(player_cmd_handler, text='players', state='*')
