# handlers/send_message_everyone.py

import logging

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy import select

from create_bot import bot
from handlers.add_player_state import get_keyboard, cancel_state
from settings import async_session_maker
from src.decorators import member_admin_state_call_check, member_admin_state_message_check
from src.player import Player
from src.utils import get_new_day_start


class FormEveryone(StatesGroup):
    message = State()


@member_admin_state_call_check
async def start_all_command(call: types.CallbackQuery, state: FSMContext):  # state не удалять
    """Отправка сообщения вообще всем членам гильдии"""
    keyboard = get_keyboard()
    await call.message.answer("Введите сообщение, которое хотите отправить всем членам гильдии.",
                              reply_markup=keyboard)
    await FormEveryone.message.set()


@member_admin_state_message_check
async def process_all_message(message: types.Message, state: FSMContext):
        data = await state.get_data()
        data['message'] = message.text  # Save the message text

        new_day_start = get_new_day_start()

        async with async_session_maker() as session:
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= new_day_start))
            all_users = query.scalars().all()

        users_from_db = {user.tg_nic: [user.tg_id, user.name] for user in all_users}

        failed_users = []  # List of users for whom message sending failed

        if users_from_db:
            # Send the message to each user
            for user_nic, user_id_name in users_from_db.items():
                try:
                    await bot.send_message(user_id_name[0], f"{user_id_name[1]}, {data['message']}")
                except Exception as e:
                    failed_users.append(user_nic)  # Add the user to the list of failures
                    logging.info(f"Failed to send message to user {user_nic}: {e}")
        if failed_users:
            await message.answer(
                "Не удалось отправить сообщения следующим пользователям: " + ", https://t.me/".join(failed_users))
        else:
            await message.answer("Сообщения были успешно отправлены всем.")
        await state.finish()


def register_handlers_message_all(dp: Dispatcher):
    dp.register_callback_query_handler(start_all_command, text='group_all')
    dp.register_message_handler(process_all_message, state=FormEveryone.message)
    dp.register_callback_query_handler(cancel_state, text="cancel",
                                       state=FormEveryone.all_states)  # Обработчик кнопки отмены
