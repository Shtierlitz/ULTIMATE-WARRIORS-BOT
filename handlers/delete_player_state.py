# handlers/delete_player_state.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton


from handlers.add_player_state import get_keyboard
from src.utils import delete_player_from_ids, is_member_admin_super


class DeletePlayer(StatesGroup):
    GET_NAME = State()
    DELETE_PLAYER = State()


async def start_delete_player(call: types.CallbackQuery, state: FSMContext):
    """Начинает сиквенцию"""
    is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
    if is_guild_member:
        if admin and super_admin:
            keyboard = get_keyboard()
            await call.message.answer("Начинаем сиквенцию удаления персонажа из ids.json\nВведите имя персонажа в игре.",
                                 reply_markup=keyboard)
            await DeletePlayer.GET_NAME.set()
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def delete_player_name(message: types.Message, state: FSMContext):
    is_guild_member, admin, super_admin = await is_member_admin_super(message=message, super_a=True)
    if is_guild_member:
        if admin and super_admin:
            try:
                # Сохраняем имя игрока в контексте состояния
                await state.update_data(player_name=message.text)
                keyboard = get_keyboard()
                delete_button = InlineKeyboardButton("Да", callback_data="delete")
                keyboard.add(delete_button)
                await message.answer(
                    f"Вы уверены, что хотите удалить игрока {message.text}?",
                    reply_markup=keyboard)  # Здесь добавляем вопрос пользователю
                await DeletePlayer.DELETE_PLAYER.set()
            except Exception as e:
                await message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def delete_player_process(call: types.CallbackQuery, state: FSMContext):
    is_guild_member, admin, super_admin = await is_member_admin_super(call, super_a=True)
    if is_guild_member:
        if admin and super_admin:
            try:
                # Извлекаем имя игрока из контекста состояния
                data = await state.get_data()
                player_name = data.get("player_name")
                # Удаление игрока
                await delete_player_from_ids(call.message, player_name)
            except Exception as e:
                await call.message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
            finally:
                # Сбрасываем состояние
                await state.finish()
        else:
            await call.message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def cancel_add_player(call: types.CallbackQuery, state: FSMContext):
    """Завершает сиквенцию добавления персонажа"""
    await state.finish()
    await call.message.answer("Удаление персонажа отменено.")


def register_handlers_delete_player(dp: Dispatcher):
    dp.register_callback_query_handler(start_delete_player, text='delete_player', state='*', is_chat_admin=True)
    dp.register_message_handler(delete_player_name, state=DeletePlayer.GET_NAME, is_chat_admin=True)
    dp.register_callback_query_handler(delete_player_process, text="delete", state=DeletePlayer.DELETE_PLAYER, is_chat_admin=True)

    dp.register_callback_query_handler(cancel_add_player, text="cancel",
                                       state=DeletePlayer.all_states)  # Обработчик кнопки отмены
