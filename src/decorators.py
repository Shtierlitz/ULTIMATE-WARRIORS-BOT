# src/decorators.py
from functools import wraps

from aiogram import types
from aiogram.dispatcher import FSMContext

from src.utils import is_member_admin_super


def member_check_message(func):
    """Декоратор на проверку членства через message"""

    @wraps(func)
    async def wrapper(message: types.Message):
        is_guild_member = message.conf.get('is_guild_member', False)
        if is_guild_member:
            try:
                return await func(message)
            except Exception as e:
                await message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper


def member_check_call(func):
    """Декоратор на проверку членства через call"""

    @wraps(func)
    async def wrapper(call: types.CallbackQuery):
        is_guild_member = call.message.conf.get('is_guild_member', False)
        if is_guild_member:
            try:
                return await func(call)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await call.message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper


def member_admin_check(func):
    """Декоратор на проверки членства и администрации"""

    @wraps(func)
    async def wrapper(call: types.CallbackQuery):
        is_guild_member, admin = await is_member_admin_super(call)
        if is_guild_member:
            if admin:
                try:
                    return await func(call)
                except Exception as e:
                    await call.message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
        else:
            await call.message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper


def member_super_admin_check(func):
    """Декоратор на проверки членства, администрации и супер-администрации"""

    @wraps(func)
    async def wrapper(call: types.CallbackQuery):
        is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
        if is_guild_member:
            if admin and super_admin:
                try:
                    return await func(call)
                except Exception as e:
                    await call.message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
        else:
            await call.message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper


def member_admin_state_call_check(func):
    """Декоратор на проверки членства, администрации для call и состояния"""

    @wraps(func)
    async def wrapper(call: types.CallbackQuery, state: FSMContext):
        is_guild_member, admin = await is_member_admin_super(call)
        if is_guild_member:
            if admin:
                try:
                    return await func(call, state)
                except Exception as e:
                    await call.message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
                await state.finish()
        else:
            await call.message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper


def member_admin_state_message_check(func):
    """Декоратор на проверки членства, администрации для call и состояния"""

    @wraps(func)
    async def wrapper(message: types.Message, state: FSMContext):
        is_guild_member, admin = await is_member_admin_super(message=message)
        if is_guild_member:
            if admin:
                try:
                    return await func(message, state)
                except Exception as e:
                    await message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
                await state.finish()

    return wrapper


def member_admin_super_state_call_check(func):
    """Декоратор на проверки членства, администрации, супер-администрации для call и состояния"""

    @wraps(func)
    async def wrapper(call: types.CallbackQuery, state: FSMContext):
        is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
        if is_guild_member:
            if admin and super_admin:
                try:
                    return await func(call, state)
                except Exception as e:
                    await call.message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
                await state.finish()
        else:
            await call.message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper

def member_admin_super_state_message_check(func):
    """Декоратор на проверки членства, администрации, супер-администрации для call и состояния"""

    @wraps(func)
    async def wrapper(message: types.Message, state: FSMContext):
        is_guild_member, admin, super_admin = await is_member_admin_super(message=message, super_a=True)
        if is_guild_member:
            if admin and super_admin:
                try:
                    return await func(message, state)
                except Exception as e:
                    await message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            else:
                await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
                await state.finish()
        else:
            await message.answer(
                "Вы не являетесь членом гильдии или не подали свой тг ID офицерам. Комманда запрещена."
                "\nДля вступления в гильдию напишите старшему офицеру в личку:\nhttps://t.me/rollbar")

    return wrapper
