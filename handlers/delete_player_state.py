# handlers/delete_player_state.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import bot
from handlers.add_player_state import get_keyboard
from src.utils import is_admin, is_super_admin, delete_player_from_ids


class DeletePlayer(StatesGroup):
    GET_NAME = State()
    DELETE_PLAYER = State()


async def start_delete_player(message: types.Message, state: FSMContext):
    """Начинает сиквенцию"""
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    tg_id = member['user']['id']
    super_admin = await is_super_admin(tg_id)
    if is_guild_member:
        if admin and super_admin:
            keyboard = get_keyboard()
            await message.answer("Начинаем сиквенцию удаления персонажа из ids.json\nВведите имя персонажа в игре.",
                                 reply_markup=keyboard)
            await DeletePlayer.GET_NAME.set()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def delete_player_name(message: types.Message, state: FSMContext):
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    tg_id = member['user']['id']
    super_admin = await is_super_admin(tg_id)
    if is_guild_member:
        if admin and super_admin:
            try:
                # Сохраняем имя игрока в контексте состояния
                await state.update_data(player_name=message.text)
                keyboard = get_keyboard()
                await message.answer(
                    f"Вы уверены, что хотите удалить игрока {message.text}? (Да/нет)",
                    reply_markup=keyboard)  # Здесь добавляем вопрос пользователю
                await DeletePlayer.DELETE_PLAYER.set()
            except Exception as e:
                await message.reply(
                    f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def delete_player_process(message: types.Message, state: FSMContext):
    is_guild_member = message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, message.from_user, message.chat)
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    tg_id = member['user']['id']
    super_admin = await is_super_admin(tg_id)
    if is_guild_member:
        if admin and super_admin:
            if message.text != 'Да':
                await message.reply(
                    f"Отмена удаления игрока.")
                await state.finish()
            else:
                try:
                    # Извлекаем имя игрока из контекста состояния
                    data = await state.get_data()
                    player_name = data.get("player_name")
                    # Удаление игрока
                    await delete_player_from_ids(message, player_name)
                except Exception as e:
                    await message.reply(
                        f"Ошибка:\n\n❌❌{e}❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")
                finally:
                    # Сбрасываем состояние
                    await state.finish()
        else:
            await message.reply(f"❌У вас нет прав для использования этой команды.❌\nОбратитесь к офицеру.")
            await state.finish()


async def cancel_add_player(call: types.CallbackQuery, state: FSMContext):
    """Завершает сиквенцию добавления персонажа"""
    await state.finish()
    await call.message.answer("Удаление персонажа отменено.")


def register_handlers_delete_player(dp: Dispatcher):
    dp.register_message_handler(start_delete_player, commands='delete_player', state='*', is_chat_admin=True)
    dp.register_message_handler(delete_player_name, state=DeletePlayer.GET_NAME, is_chat_admin=True)
    dp.register_message_handler(delete_player_process, state=DeletePlayer.DELETE_PLAYER, is_chat_admin=True)
    dp.register_callback_query_handler(cancel_add_player, text="cancel",
                                       state=DeletePlayer.all_states)  # Обработчик кнопки отмены
