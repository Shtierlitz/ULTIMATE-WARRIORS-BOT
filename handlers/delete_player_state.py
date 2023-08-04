# handlers/delete_player_state.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton

from handlers.add_player_state import get_keyboard
from src.decorators import member_admin_super_state_call_check, member_admin_super_state_message_check
from src.utils import delete_player_from_ids


class DeletePlayer(StatesGroup):
    GET_NAME = State()
    DELETE_PLAYER = State()


@member_admin_super_state_call_check
async def start_delete_player(call: types.CallbackQuery, state: FSMContext):  # state не удалять!
    """Начинает сиквенцию"""
    keyboard = get_keyboard()
    await call.message.answer("Начинаем сиквенцию удаления персонажа из ids.json\nВведите имя персонажа в игре.",
                              reply_markup=keyboard)
    await DeletePlayer.GET_NAME.set()


@member_admin_super_state_message_check
async def delete_player_name(message: types.Message, state: FSMContext):
    # Сохраняем имя игрока в контексте состояния
    await state.update_data(player_name=message.text)
    keyboard = get_keyboard()
    delete_button = InlineKeyboardButton("Да", callback_data="delete")
    keyboard.add(delete_button)
    await message.answer(
        f"Вы уверены, что хотите удалить игрока {message.text}❔",
        reply_markup=keyboard)  # Здесь добавляем вопрос пользователю
    await DeletePlayer.DELETE_PLAYER.set()


@member_admin_super_state_call_check
async def delete_player_process(call: types.CallbackQuery, state: FSMContext):
    # Извлекаем имя игрока из контекста состояния
    data = await state.get_data()
    player_name = data.get("player_name")
    # Удаление игрока
    action = await delete_player_from_ids(call.message, player_name)
    if not action:
        await call.message.answer("❌ Удаление персонажа отменено.")
        await state.finish()


async def cancel_add_player(call: types.CallbackQuery, state: FSMContext):
    """Завершает сиквенцию добавления персонажа"""
    await state.finish()
    await call.message.answer("❌ Удаление персонажа отменено.")


def register_handlers_delete_player(dp: Dispatcher):
    dp.register_callback_query_handler(start_delete_player, text='delete_player', state='*', is_chat_admin=True)
    dp.register_message_handler(delete_player_name, state=DeletePlayer.GET_NAME, is_chat_admin=True)
    dp.register_callback_query_handler(delete_player_process, text="delete", state=DeletePlayer.DELETE_PLAYER,
                                       is_chat_admin=True)

    dp.register_callback_query_handler(cancel_add_player, text="cancel",
                                       state=DeletePlayer.all_states)  # Обработчик кнопки отмены
